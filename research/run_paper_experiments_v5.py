from __future__ import annotations

import csv
import hashlib
import json
import platform
import random
import statistics
import subprocess
import time
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROTOCOL_VERSION = "5.0"

SIZES = (1_000, 10_000, 100_000)
SEEDS = (1301, 2609, 3911, 5209, 6521)
INTENSITIES = (0.01, 0.05, 0.10)

REPEATS = 7
CHECKPOINT_FRACTION = 0.50
REPLAY_FRACTION = 0.50
CONTROL_INTENSITY = 0.05

STRATEGIES = (
    "S1_minimal",
    "S2_temporal",
    "S3_recovery",
    "S4_full",
)

CONTROL_FAULTS = (
    "duplicate",
    "null_key",
    "late",
    "conflict",
    "recovery",
)

BASE_TS = datetime(2026, 4, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class StrategySpec:
    ordinary_dedup: bool
    validate_required_key: bool
    temporal_resolution: bool
    idempotent_recovery: bool


SPECS = {
    "S1_minimal": StrategySpec(True, True, False, False),
    "S2_temporal": StrategySpec(True, True, True, False),
    "S3_recovery": StrategySpec(True, True, False, True),
    "S4_full": StrategySpec(True, True, True, True),
}


def git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return "UNKNOWN"


def count_for(total: int, rate: float) -> int:
    if total <= 0 or rate <= 0:
        return 0
    return min(total, max(1, round(total * rate)))


def choose(rng: random.Random, values, k: int):
    values = list(values)
    if k <= 0:
        return []
    if k >= len(values):
        return list(values)
    return rng.sample(values, k)


def canonical_dataset(n: int, seed: int):
    rng = random.Random(seed)
    entity_count = max(10, n // 20)

    rows = []
    for i in range(n):
        entity_num = i % entity_count
        rows.append(
            {
                "event_id": f"e{i}",
                "entity_id": f"entity-{entity_num}",
                "business_key": f"k{i}",
                "event_ts": BASE_TS + timedelta(seconds=i),
                "value": rng.randint(1, 1_000_000),
                "fault_tags": tuple(),
                "is_recovery_replay": False,
            }
        )

    return rows


def build_oracle(canonical):
    expected_ids = set()
    expected_entities = set()
    latest = {}

    for row in canonical:
        expected_ids.add(row["event_id"])
        expected_entities.add(row["entity_id"])

        current = latest.get(row["entity_id"])
        if current is None or row["event_ts"] > current["event_ts"]:
            latest[row["entity_id"]] = deepcopy(row)

    return {
        "expected_ids": expected_ids,
        "expected_entities": expected_entities,
        "latest_state": latest,
    }


def add_duplicate_fault(work, rng, rate):
    k = count_for(len(work), rate)
    selected = choose(rng, work, k)

    duplicates = []
    for row in selected:
        copy = deepcopy(row)
        copy["fault_tags"] = tuple(
            sorted(set(copy["fault_tags"]) | {"duplicate"})
        )
        duplicates.append(copy)

    work.extend(duplicates)
    return len(duplicates)


def add_null_fault(work, canonical_ids, rng, rate):
    eligible = [x for x in work if x["event_id"] in canonical_ids]
    selected_ids = {
        x["event_id"]
        for x in choose(rng, eligible, count_for(len(eligible), rate))
    }

    for row in work:
        if row["event_id"] in selected_ids:
            row["business_key"] = None
            row["fault_tags"] = tuple(
                sorted(set(row["fault_tags"]) | {"null_key"})
            )

    return len(selected_ids)


def add_late_fault(work, canonical_ids, rng, rate):
    eligible_ids = list(
        dict.fromkeys(
            x["event_id"]
            for x in work
            if x["event_id"] in canonical_ids
        )
    )

    selected_ids = set(
        choose(rng, eligible_ids, count_for(len(eligible_ids), rate))
    )

    if not selected_ids:
        return 0

    normal = []
    late = []

    for row in work:
        if row["event_id"] in selected_ids:
            copy = deepcopy(row)
            copy["fault_tags"] = tuple(
                sorted(set(copy["fault_tags"]) | {"late"})
            )
            late.append(copy)
        else:
            normal.append(row)

    work[:] = normal + late
    return len(selected_ids)


def add_conflict_fault(work, oracle, rng, rate):
    entities = sorted(oracle["expected_entities"])
    target = count_for(len(entities), rate)
    selected_entities = choose(rng, entities, target)

    conflicts = []

    for idx, entity_id in enumerate(selected_entities):
        canonical_latest = oracle["latest_state"][entity_id]

        conflict = {
            "event_id": f"conflict-{entity_id}-{idx}",
            "entity_id": entity_id,
            "business_key": f"conflict-key-{entity_id}-{idx}",
            "event_ts": canonical_latest["event_ts"] - timedelta(microseconds=1),
            "value": -(idx + 1),
            "fault_tags": ("conflict",),
            "is_recovery_replay": False,
        }

        conflicts.append(conflict)

    work.extend(conflicts)
    return len(conflicts)


def inject_non_recovery_faults(
    canonical,
    oracle,
    seed: int,
    duplicate_rate: float,
    null_rate: float,
    late_rate: float,
    conflict_rate: float,
):
    rng = random.Random(seed + 404)
    work = deepcopy(canonical)

    realized = {
        "duplicate": 0,
        "null_key": 0,
        "late": 0,
        "conflict": 0,
    }

    canonical_ids = oracle["expected_ids"]

    if conflict_rate > 0:
        realized["conflict"] = add_conflict_fault(
            work, oracle, rng, conflict_rate
        )

    if late_rate > 0:
        realized["late"] = add_late_fault(
            work, canonical_ids, rng, late_rate
        )

    if null_rate > 0:
        realized["null_key"] = add_null_fault(
            work, canonical_ids, rng, null_rate
        )

    if duplicate_rate > 0:
        realized["duplicate"] = add_duplicate_fault(
            work, rng, duplicate_rate
        )

    return work, realized


def split_checkpoint(work):
    cut = max(1, round(len(work) * CHECKPOINT_FRACTION))
    cut = min(cut, len(work))
    return deepcopy(work[:cut]), deepcopy(work[cut:])


def process_pre_checkpoint(rows, strategy):
    spec = SPECS[strategy]

    seen = set()
    valid = []
    counters = Counter()

    for row in rows:
        if spec.validate_required_key and row["business_key"] is None:
            counters["null_key_recognized"] += 1
            counters["null_key_contained"] += 1
            continue

        if spec.ordinary_dedup and row["event_id"] in seen:
            counters["duplicate_recognized"] += 1
            counters["duplicate_contained"] += 1
            continue

        seen.add(row["event_id"])
        valid.append(deepcopy(row))

    state = materialize_state(valid, spec.temporal_resolution)

    return {
        "valid": valid,
        "state": state,
        "committed_event_ids": set(x["event_id"] for x in valid),
        "seen_event_ids": set(seen),
        "counters": counters,
    }


def construct_recovery_restart(pre_result, remaining):
    committed_ids = sorted(pre_result["committed_event_ids"])

    replay_n = count_for(len(committed_ids), REPLAY_FRACTION)
    replay_ids = set(committed_ids[:replay_n])

    source_by_id = {}
    for row in pre_result["valid"]:
        source_by_id.setdefault(row["event_id"], row)

    replay = []

    for event_id in committed_ids:
        if event_id not in replay_ids:
            continue

        row = deepcopy(source_by_id[event_id])
        row["is_recovery_replay"] = True
        row["fault_tags"] = tuple(
            sorted(set(row["fault_tags"]) | {"recovery_replay"})
        )
        replay.append(row)

    restart_work = replay + deepcopy(remaining)

    return restart_work, {
        "recovery_replay_count": len(replay),
        "already_committed_replay_count": len(replay),
    }


def process_restart(pre_result, restart_work, strategy):
    spec = SPECS[strategy]

    valid = deepcopy(pre_result["valid"])
    seen = set(pre_result["seen_event_ids"])
    committed = set(pre_result["committed_event_ids"])
    counters = Counter(pre_result["counters"])

    recovery_replays_suppressed = 0
    recovery_replays_reprocessed = 0

    for row in restart_work:
        recovery_copy = bool(row.get("is_recovery_replay"))

        if spec.validate_required_key and row["business_key"] is None:
            counters["null_key_recognized"] += 1
            counters["null_key_contained"] += 1
            continue

        if recovery_copy and row["event_id"] in committed:
            counters["recovery_replay_recognized"] += 1

            if spec.idempotent_recovery:
                recovery_replays_suppressed += 1
                counters["recovery_replay_contained"] += 1
                continue

            recovery_replays_reprocessed += 1
            valid.append(deepcopy(row))
            continue

        if spec.ordinary_dedup and row["event_id"] in seen:
            counters["duplicate_recognized"] += 1
            counters["duplicate_contained"] += 1
            continue

        seen.add(row["event_id"])
        valid.append(deepcopy(row))

    state = materialize_state(valid, spec.temporal_resolution)

    return {
        "valid": valid,
        "state": state,
        "counters": counters,
        "recovery_replays_suppressed": recovery_replays_suppressed,
        "recovery_replays_reprocessed": recovery_replays_reprocessed,
    }


def process_without_recovery(work, strategy):
    spec = SPECS[strategy]

    seen = set()
    valid = []
    counters = Counter()

    for row in work:
        if spec.validate_required_key and row["business_key"] is None:
            counters["null_key_recognized"] += 1
            counters["null_key_contained"] += 1
            continue

        if spec.ordinary_dedup and row["event_id"] in seen:
            counters["duplicate_recognized"] += 1
            counters["duplicate_contained"] += 1
            continue

        seen.add(row["event_id"])
        valid.append(deepcopy(row))

    state = materialize_state(valid, spec.temporal_resolution)

    return {
        "valid": valid,
        "state": state,
        "counters": counters,
        "recovery_replays_suppressed": 0,
        "recovery_replays_reprocessed": 0,
    }


def materialize_state(valid, temporal_resolution: bool):
    state = {}

    if temporal_resolution:
        for row in valid:
            current = state.get(row["entity_id"])
            if current is None or row["event_ts"] > current["event_ts"]:
                state[row["entity_id"]] = row
    else:
        for row in valid:
            state[row["entity_id"]] = row

    return state


def logical_signature(row):
    return (
        row["event_id"],
        row["entity_id"],
        row["business_key"],
        row["event_ts"],
        row["value"],
    )


def compute_metrics(
    result,
    oracle,
    realized,
    recovery_meta,
):
    valid = result["valid"]
    state = result["state"]

    expected_ids = oracle["expected_ids"]
    expected_entities = oracle["expected_entities"]
    oracle_state = oracle["latest_state"]

    entities_matching = 0
    stale_state_count = 0

    for entity_id in expected_entities:
        actual = state.get(entity_id)
        expected = oracle_state[entity_id]

        if actual is not None and logical_signature(actual) == logical_signature(expected):
            entities_matching += 1
        else:
            stale_state_count += 1

    canonical_freq = Counter(
        row["event_id"]
        for row in valid
        if row["event_id"] in expected_ids
    )

    duplicate_leakage_count = sum(
        max(0, count - 1)
        for count in canonical_freq.values()
    )

    invalid_key_leakage_count = sum(
        1 for row in valid if row["business_key"] is None
    )

    recovered_ids = {
        row["event_id"]
        for row in valid
        if row["event_id"] in expected_ids
    }

    recovered_expected_count = len(recovered_ids)
    false_rejection_count = len(expected_ids - recovered_ids)

    already_committed = recovery_meta["already_committed_replay_count"]
    recovery_reprocessed = result["recovery_replays_reprocessed"]

    recovery_duplicate_effect_count = recovery_reprocessed

    oracle_entities = len(expected_entities)
    duplicate_denominator = max(
        1,
        realized["duplicate"] + already_committed,
    )
    invalid_key_denominator = max(1, realized["null_key"])
    recovery_denominator = max(1, len(expected_ids))
    recovery_effect_denominator = max(1, already_committed)

    return {
        "oracle_entities": oracle_entities,
        "entities_matching_oracle": entities_matching,
        "duplicate_leakage_count": duplicate_leakage_count,
        "duplicate_denominator": duplicate_denominator,
        "invalid_key_leakage_count": invalid_key_leakage_count,
        "invalid_key_denominator": invalid_key_denominator,
        "stale_state_count": stale_state_count,
        "stale_state_denominator": max(1, oracle_entities),
        "recovered_expected_count": recovered_expected_count,
        "recovery_denominator": recovery_denominator,
        "false_rejection_count": false_rejection_count,
        "false_rejection_denominator": recovery_denominator,
        "recovery_replay_count": recovery_meta["recovery_replay_count"],
        "already_committed_replay_count": already_committed,
        "recovery_replays_suppressed": result["recovery_replays_suppressed"],
        "recovery_replays_reprocessed": recovery_reprocessed,
        "recovery_duplicate_effect_count": recovery_duplicate_effect_count,
        "recovery_duplicate_effect_denominator": recovery_effect_denominator,
        "state_correctness_rate": entities_matching / max(1, oracle_entities),
        "duplicate_leakage_rate": duplicate_leakage_count / duplicate_denominator,
        "invalid_key_leakage_rate": invalid_key_leakage_count
        / invalid_key_denominator,
        "stale_state_rate": stale_state_count / max(1, oracle_entities),
        "recovery_completeness_rate": recovered_expected_count
        / recovery_denominator,
        "false_rejection_rate": false_rejection_count
        / recovery_denominator,
        "recovery_duplicate_effect_rate": recovery_duplicate_effect_count
        / recovery_effect_denominator,
    }


def fault_handling_fields(realized, result, metrics):
    counters = result["counters"]

    injected = {
        "duplicate": realized["duplicate"],
        "null_key": realized["null_key"],
        "late": realized["late"],
        "conflict": realized["conflict"],
        "recovery": metrics["already_committed_replay_count"],
    }

    recognized = {
        "duplicate": counters["duplicate_recognized"],
        "null_key": counters["null_key_recognized"],
        "late": 0,
        "conflict": 0,
        "recovery": counters["recovery_replay_recognized"],
    }

    contained = {
        "duplicate": counters["duplicate_contained"],
        "null_key": counters["null_key_contained"],
        "late": 0,
        "conflict": 0,
        "recovery": counters["recovery_replay_contained"],
    }

    return {
        "duplicate_faults_injected": injected["duplicate"],
        "duplicate_faults_recognized": recognized["duplicate"],
        "duplicate_faults_contained": contained["duplicate"],
        "null_key_faults_injected": injected["null_key"],
        "null_key_faults_recognized": recognized["null_key"],
        "null_key_faults_contained": contained["null_key"],
        "late_faults_injected": injected["late"],
        "late_faults_recognized": recognized["late"],
        "late_faults_contained": contained["late"],
        "conflict_faults_injected": injected["conflict"],
        "conflict_faults_recognized": recognized["conflict"],
        "conflict_faults_contained": contained["conflict"],
        "recovery_faults_injected": injected["recovery"],
        "recovery_faults_recognized": recognized["recovery"],
        "recovery_faults_contained": contained["recovery"],
    }


def execute_once(
    work,
    oracle,
    strategy,
    recovery_enabled,
):
    if not recovery_enabled:
        result = process_without_recovery(deepcopy(work), strategy)
        recovery_meta = {
            "recovery_replay_count": 0,
            "already_committed_replay_count": 0,
        }
        return result, recovery_meta

    pre, remaining = split_checkpoint(work)
    pre_result = process_pre_checkpoint(pre, strategy)

    restart_work, recovery_meta = construct_recovery_restart(
        pre_result,
        remaining,
    )

    result = process_restart(
        pre_result,
        restart_work,
        strategy,
    )

    return result, recovery_meta


def timed_execution(
    work,
    oracle,
    strategy,
    recovery_enabled,
):
    durations = []

    final_result = None
    final_recovery_meta = None

    for _ in range(REPEATS):
        start = time.perf_counter_ns()

        result, recovery_meta = execute_once(
            work,
            oracle,
            strategy,
            recovery_enabled,
        )

        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        durations.append(elapsed_ms)

        final_result = result
        final_recovery_meta = recovery_meta

    return (
        final_result,
        final_recovery_meta,
        statistics.median(durations),
        statistics.mean(durations),
    )


def build_observation(
    *,
    experiment_kind,
    fault_condition,
    dataset_size,
    seed,
    intensity,
    strategy,
    canonical,
    oracle,
    work,
    realized,
    recovery_enabled,
    commit_sha,
):
    result, recovery_meta, runtime_median, runtime_mean = timed_execution(
        work,
        oracle,
        strategy,
        recovery_enabled,
    )

    metrics = compute_metrics(
        result,
        oracle,
        realized,
        recovery_meta,
    )

    handling = fault_handling_fields(
        realized,
        result,
        metrics,
    )

    return {
        "schema_version": PROTOCOL_VERSION,
        "experiment_kind": experiment_kind,
        "fault_condition": fault_condition,
        "dataset_size": dataset_size,
        "seed": seed,
        "nominal_intensity": intensity,
        "checkpoint_fraction": CHECKPOINT_FRACTION,
        "replay_fraction": REPLAY_FRACTION,
        "strategy": strategy,
        "realized_duplicate": realized["duplicate"],
        "realized_null_key": realized["null_key"],
        "realized_late": realized["late"],
        "realized_conflict_entities": realized["conflict"],
        **metrics,
        **handling,
        "runtime_ms_median": runtime_median,
        "runtime_ms_mean": runtime_mean,
        "timing_repeats": REPEATS,
        "commit_sha": commit_sha,
        "python": platform.python_version(),
    }


def principal_observations(commit_sha):
    observations = []

    for n in SIZES:
        for seed in SEEDS:
            canonical = canonical_dataset(n, seed)
            oracle = build_oracle(canonical)

            for intensity in INTENSITIES:
                work, realized = inject_non_recovery_faults(
                    canonical,
                    oracle,
                    seed,
                    duplicate_rate=intensity,
                    null_rate=intensity,
                    late_rate=intensity,
                    conflict_rate=intensity,
                )

                for strategy in STRATEGIES:
                    observations.append(
                        build_observation(
                            experiment_kind="principal",
                            fault_condition="compound",
                            dataset_size=n,
                            seed=seed,
                            intensity=intensity,
                            strategy=strategy,
                            canonical=canonical,
                            oracle=oracle,
                            work=work,
                            realized=realized,
                            recovery_enabled=True,
                            commit_sha=commit_sha,
                        )
                    )

    return observations


def control_observations(commit_sha):
    observations = []

    for n in SIZES:
        for seed in SEEDS:
            canonical = canonical_dataset(n, seed)
            oracle = build_oracle(canonical)

            for fault in CONTROL_FAULTS:
                rates = {
                    "duplicate": 0.0,
                    "null_key": 0.0,
                    "late": 0.0,
                    "conflict": 0.0,
                }

                recovery_enabled = fault == "recovery"

                if fault != "recovery":
                    rates[fault] = CONTROL_INTENSITY

                work, realized = inject_non_recovery_faults(
                    canonical,
                    oracle,
                    seed,
                    duplicate_rate=rates["duplicate"],
                    null_rate=rates["null_key"],
                    late_rate=rates["late"],
                    conflict_rate=rates["conflict"],
                )

                for strategy in STRATEGIES:
                    observations.append(
                        build_observation(
                            experiment_kind="single_fault_control",
                            fault_condition=fault,
                            dataset_size=n,
                            seed=seed,
                            intensity=(
                                REPLAY_FRACTION
                                if fault == "recovery"
                                else CONTROL_INTENSITY
                            ),
                            strategy=strategy,
                            canonical=canonical,
                            oracle=oracle,
                            work=work,
                            realized=realized,
                            recovery_enabled=recovery_enabled,
                            commit_sha=commit_sha,
                        )
                    )

    return observations


def validate_observations(rows):
    expected_principal = (
        len(SIZES)
        * len(SEEDS)
        * len(INTENSITIES)
        * len(STRATEGIES)
    )

    expected_controls = (
        len(SIZES)
        * len(SEEDS)
        * len(CONTROL_FAULTS)
        * len(STRATEGIES)
    )

    principal = [
        x for x in rows
        if x["experiment_kind"] == "principal"
    ]

    controls = [
        x for x in rows
        if x["experiment_kind"] == "single_fault_control"
    ]

    if len(principal) != expected_principal:
        raise AssertionError(
            f"principal count {len(principal)} != {expected_principal}"
        )

    if len(controls) != expected_controls:
        raise AssertionError(
            f"control count {len(controls)} != {expected_controls}"
        )

    rate_fields = (
        "state_correctness_rate",
        "duplicate_leakage_rate",
        "invalid_key_leakage_rate",
        "stale_state_rate",
        "recovery_completeness_rate",
        "false_rejection_rate",
        "recovery_duplicate_effect_rate",
    )

    for row in rows:
        for field in rate_fields:
            value = row[field]
            if not 0.0 <= value <= 1.0:
                raise AssertionError(
                    f"{field} outside [0,1]: {value}"
                )

        if row["already_committed_replay_count"] > 0:
            if row["recovery_duplicate_effect_denominator"] <= 0:
                raise AssertionError(
                    "non-zero recovery workload has zero denominator"
                )


def summarize(rows):
    groups = {}

    for row in rows:
        key = (
            row["experiment_kind"],
            row["fault_condition"],
            row["dataset_size"],
            row["nominal_intensity"],
            row["strategy"],
        )
        groups.setdefault(key, []).append(row)

    summary = []

    metric_fields = (
        "state_correctness_rate",
        "duplicate_leakage_rate",
        "invalid_key_leakage_rate",
        "stale_state_rate",
        "recovery_completeness_rate",
        "false_rejection_rate",
        "recovery_duplicate_effect_rate",
        "runtime_ms_median",
        "runtime_ms_mean",
    )

    for key in sorted(groups, key=str):
        items = groups[key]

        record = {
            "experiment_kind": key[0],
            "fault_condition": key[1],
            "dataset_size": key[2],
            "nominal_intensity": key[3],
            "strategy": key[4],
            "observations": len(items),
        }

        for field in metric_fields:
            values = [x[field] for x in items]
            record[f"{field}_mean"] = statistics.mean(values)
            record[f"{field}_median"] = statistics.median(values)

        summary.append(record)

    return summary


def write_artifacts(rows, failures, commit_sha):
    root = Path(__file__).resolve().parent
    results_dir = root / "results"
    raw_dir = results_dir / "raw"

    results_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    raw_path = raw_dir / f"paper-suite-v5-{stamp}.csv"
    summary_path = results_dir / f"paper-suite-v5-{stamp}-summary.json"
    failure_path = results_dir / f"paper-suite-v5-{stamp}-failures.json"

    if not rows:
        raise AssertionError("no observations produced")

    fieldnames = list(rows[0].keys())

    with raw_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    raw_sha256 = hashlib.sha256(raw_path.read_bytes()).hexdigest()

    summary_payload = {
        "schema_version": PROTOCOL_VERSION,
        "protocol": "research/EXPERIMENT_PROTOCOL_V5.md",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "commit_sha": commit_sha,
        "python": platform.python_version(),
        "sizes": list(SIZES),
        "seeds": list(SEEDS),
        "nominal_intensities": list(INTENSITIES),
        "strategies": list(STRATEGIES),
        "checkpoint_fraction": CHECKPOINT_FRACTION,
        "replay_fraction": REPLAY_FRACTION,
        "timing_repeats": REPEATS,
        "observation_count": len(rows),
        "principal_observations": sum(
            x["experiment_kind"] == "principal"
            for x in rows
        ),
        "control_observations": sum(
            x["experiment_kind"] == "single_fault_control"
            for x in rows
        ),
        "failure_count": len(failures),
        "raw_sha256": raw_sha256,
        "summary": summarize(rows),
    }

    summary_path.write_text(
        json.dumps(summary_payload, indent=2, default=str),
        encoding="utf-8",
    )

    failure_path.write_text(
        json.dumps(failures, indent=2, default=str),
        encoding="utf-8",
    )

    return raw_path, summary_path, failure_path


def main():
    commit_sha = git_sha()
    failures = []
    rows = []

    print(
        f"V5 execution starting | commit={commit_sha} | "
        "expected observations=480",
        flush=True,
    )

    try:
        print(
            "V5 progress: starting principal matrix (180 observations)...",
            flush=True,
        )
        rows.extend(principal_observations(commit_sha))
        print(
            "V5 progress: principal matrix complete (180/480).",
            flush=True,
        )
    except Exception as exc:
        failures.append(
            {
                "stage": "principal",
                "error": repr(exc),
            }
        )
        raise

    try:
        print(
            "V5 progress: starting isolated controls (300 observations)...",
            flush=True,
        )
        rows.extend(control_observations(commit_sha))
        print(
            "V5 progress: controls complete (480/480).",
            flush=True,
        )
    except Exception as exc:
        failures.append(
            {
                "stage": "controls",
                "error": repr(exc),
            }
        )
        raise

    validate_observations(rows)

    raw_path, summary_path, failure_path = write_artifacts(
        rows,
        failures,
        commit_sha,
    )

    print(
        json.dumps(
            {
                "raw": str(raw_path),
                "summary": str(summary_path),
                "failures": str(failure_path),
                "observations": len(rows),
                "principal_observations": sum(
                    x["experiment_kind"] == "principal"
                    for x in rows
                ),
                "control_observations": sum(
                    x["experiment_kind"] == "single_fault_control"
                    for x in rows
                ),
                "failure_count": len(failures),
                "commit_sha": commit_sha,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()