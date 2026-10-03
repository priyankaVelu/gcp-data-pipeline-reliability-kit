from __future__ import annotations

import importlib.util
import sys
from copy import deepcopy
from pathlib import Path


RUNNER_PATH = Path(__file__).with_name("run_paper_experiments_v5.py")

spec = importlib.util.spec_from_file_location(
    "run_paper_experiments_v5",
    RUNNER_PATH,
)
v5 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v5
spec.loader.exec_module(v5)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def test_frozen_constants():
    check(v5.PROTOCOL_VERSION == "5.0", "protocol version changed")
    check(v5.SIZES == (1_000, 10_000, 100_000), "sizes changed")
    check(
        v5.SEEDS == (1301, 2609, 3911, 5209, 6521),
        "seeds changed",
    )
    check(
        v5.INTENSITIES == (0.01, 0.05, 0.10),
        "intensities changed",
    )
    check(v5.REPEATS == 7, "timing repetitions changed")
    check(v5.CHECKPOINT_FRACTION == 0.50, "checkpoint changed")
    check(v5.REPLAY_FRACTION == 0.50, "replay changed")
    check(v5.CONTROL_INTENSITY == 0.05, "control intensity changed")

    check(
        v5.STRATEGIES
        == (
            "S1_minimal",
            "S2_temporal",
            "S3_recovery",
            "S4_full",
        ),
        "strategy matrix changed",
    )

    check(
        v5.CONTROL_FAULTS
        == (
            "duplicate",
            "null_key",
            "late",
            "conflict",
            "recovery",
        ),
        "control fault matrix changed",
    )


def test_strategy_definitions():
    s1 = v5.SPECS["S1_minimal"]
    s2 = v5.SPECS["S2_temporal"]
    s3 = v5.SPECS["S3_recovery"]
    s4 = v5.SPECS["S4_full"]

    check(s1.ordinary_dedup, "S1 must deduplicate ordinary duplicates")
    check(s1.validate_required_key, "S1 must validate keys")
    check(not s1.temporal_resolution, "S1 must be non-temporal")
    check(not s1.idempotent_recovery, "S1 must be non-idempotent")

    check(s2.ordinary_dedup, "S2 ordinary dedup missing")
    check(s2.validate_required_key, "S2 validation missing")
    check(s2.temporal_resolution, "S2 must be temporal")
    check(not s2.idempotent_recovery, "S2 must be non-idempotent")

    check(s3.ordinary_dedup, "S3 ordinary dedup missing")
    check(s3.validate_required_key, "S3 validation missing")
    check(not s3.temporal_resolution, "S3 must be non-temporal")
    check(s3.idempotent_recovery, "S3 must be recovery-idempotent")

    check(s4.ordinary_dedup, "S4 ordinary dedup missing")
    check(s4.validate_required_key, "S4 validation missing")
    check(s4.temporal_resolution, "S4 must be temporal")
    check(s4.idempotent_recovery, "S4 must be recovery-idempotent")


def test_canonical_determinism():
    a = v5.canonical_dataset(1_000, 1301)
    b = v5.canonical_dataset(1_000, 1301)

    check(a == b, "canonical generation is not deterministic")
    check(len(a) == 1_000, "canonical size incorrect")

    ids = [x["event_id"] for x in a]
    check(len(ids) == len(set(ids)), "canonical event IDs not unique")


def test_oracle_independence():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    before_ids = set(oracle["expected_ids"])
    before_state = deepcopy(oracle["latest_state"])

    work, _ = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        duplicate_rate=0.05,
        null_rate=0.05,
        late_rate=0.05,
        conflict_rate=0.05,
    )

    work[0]["business_key"] = "MUTATED-AFTER-ORACLE"

    check(
        oracle["expected_ids"] == before_ids,
        "fault workload mutated oracle membership",
    )
    check(
        oracle["latest_state"] == before_state,
        "fault workload mutated oracle state",
    )


def test_fault_injection_determinism():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    a, ra = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        0.05,
        0.05,
        0.05,
        0.05,
    )
    b, rb = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        0.05,
        0.05,
        0.05,
        0.05,
    )

    check(a == b, "fault injection is not deterministic")
    check(ra == rb, "realized fault counts are not deterministic")


def test_conflict_entity_semantics():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    entity_count = len(oracle["expected_entities"])
    check(entity_count == 50, "unexpected entity count for n=1000")

    expected = {
        0.01: v5.count_for(entity_count, 0.01),
        0.05: v5.count_for(entity_count, 0.05),
        0.10: v5.count_for(entity_count, 0.10),
    }

    for rate, expected_count in expected.items():
        _, realized = v5.inject_non_recovery_faults(
            canonical,
            oracle,
            1301,
            duplicate_rate=0,
            null_rate=0,
            late_rate=0,
            conflict_rate=rate,
        )

        check(
            realized["conflict"] == expected_count,
            f"conflict entity semantics incorrect at {rate}",
        )


def recovery_fixture(strategy):
    canonical = v5.canonical_dataset(100, 1301)
    oracle = v5.build_oracle(canonical)

    pre, remaining = v5.split_checkpoint(canonical)
    pre_result = v5.process_pre_checkpoint(pre, strategy)

    restart_work, recovery_meta = v5.construct_recovery_restart(
        pre_result,
        remaining,
    )

    result = v5.process_restart(
        pre_result,
        restart_work,
        strategy,
    )

    realized = {
        "duplicate": 0,
        "null_key": 0,
        "late": 0,
        "conflict": 0,
    }

    metrics = v5.compute_metrics(
        result,
        oracle,
        realized,
        recovery_meta,
    )

    return canonical, oracle, pre_result, restart_work, result, recovery_meta, metrics


def test_committed_before_replay():
    (
        _,
        _,
        pre_result,
        restart_work,
        _,
        recovery_meta,
        _,
    ) = recovery_fixture("S1_minimal")

    committed = pre_result["committed_event_ids"]

    replay_rows = [
        x for x in restart_work
        if x["is_recovery_replay"]
    ]

    check(len(committed) > 0, "checkpoint committed nothing")
    check(len(replay_rows) > 0, "recovery replay population is empty")

    check(
        recovery_meta["already_committed_replay_count"] > 0,
        "already-committed replay denominator is zero",
    )

    check(
        all(x["event_id"] in committed for x in replay_rows),
        "recovery replay contains an identity not committed before interruption",
    )


def test_recovery_identifiability():
    results = {}

    for strategy in v5.STRATEGIES:
        (
            _,
            _,
            _,
            _,
            result,
            recovery_meta,
            metrics,
        ) = recovery_fixture(strategy)

        check(
            recovery_meta["already_committed_replay_count"] > 0,
            f"{strategy}: zero committed replay denominator",
        )

        results[strategy] = {
            "suppressed": result["recovery_replays_suppressed"],
            "reprocessed": result["recovery_replays_reprocessed"],
            "effect_count": metrics["recovery_duplicate_effect_count"],
            "effect_rate": metrics["recovery_duplicate_effect_rate"],
            "completeness": metrics["recovery_completeness_rate"],
        }

    for strategy in ("S1_minimal", "S2_temporal"):
        r = results[strategy]

        check(
            r["reprocessed"] > 0,
            f"{strategy}: non-idempotent recovery produced no replay effect",
        )
        check(
            r["effect_count"] > 0,
            f"{strategy}: recovery effect not observable",
        )
        check(
            r["effect_rate"] > 0,
            f"{strategy}: recovery effect rate must be > 0",
        )

    for strategy in ("S3_recovery", "S4_full"):
        r = results[strategy]

        check(
            r["suppressed"] > 0,
            f"{strategy}: idempotent recovery suppressed nothing",
        )
        check(
            r["reprocessed"] == 0,
            f"{strategy}: committed replay was reprocessed",
        )
        check(
            r["effect_count"] == 0,
            f"{strategy}: duplicate recovery effect leaked",
        )
        check(
            r["effect_rate"] == 0,
            f"{strategy}: recovery effect rate must equal 0",
        )

    check(
        results["S1_minimal"]["completeness"] == 1.0,
        "S1 recovery lost canonical membership",
    )
    check(
        results["S3_recovery"]["completeness"] == 1.0,
        "S3 recovery lost canonical membership",
    )


def test_duplicate_control():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    work, realized = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        duplicate_rate=0.05,
        null_rate=0,
        late_rate=0,
        conflict_rate=0,
    )

    check(realized["duplicate"] > 0, "duplicate control injected nothing")

    for strategy in v5.STRATEGIES:
        result, recovery_meta = v5.execute_once(
            work,
            oracle,
            strategy,
            False,
        )

        metrics = v5.compute_metrics(
            result,
            oracle,
            realized,
            recovery_meta,
        )

        check(
            metrics["duplicate_leakage_count"] == 0,
            f"{strategy}: ordinary duplicate leaked",
        )


def test_null_control():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    work, realized = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        duplicate_rate=0,
        null_rate=0.05,
        late_rate=0,
        conflict_rate=0,
    )

    check(realized["null_key"] > 0, "null control injected nothing")

    for strategy in v5.STRATEGIES:
        result, recovery_meta = v5.execute_once(
            work,
            oracle,
            strategy,
            False,
        )

        metrics = v5.compute_metrics(
            result,
            oracle,
            realized,
            recovery_meta,
        )

        check(
            metrics["invalid_key_leakage_count"] == 0,
            f"{strategy}: invalid key leaked",
        )


def test_late_control_temporal_distinction():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    work, realized = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        duplicate_rate=0,
        null_rate=0,
        late_rate=0.05,
        conflict_rate=0,
    )

    check(realized["late"] > 0, "late control injected nothing")

    values = {}

    for strategy in v5.STRATEGIES:
        result, recovery_meta = v5.execute_once(
            work,
            oracle,
            strategy,
            False,
        )

        metrics = v5.compute_metrics(
            result,
            oracle,
            realized,
            recovery_meta,
        )

        values[strategy] = metrics["state_correctness_rate"]

    check(
        values["S2_temporal"] >= values["S1_minimal"],
        "temporal strategy worse than matched non-temporal late control",
    )
    check(
        values["S4_full"] >= values["S3_recovery"],
        "full strategy worse than recovery strategy on late control",
    )


def test_conflict_control_temporal_distinction():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    work, realized = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        duplicate_rate=0,
        null_rate=0,
        late_rate=0,
        conflict_rate=0.05,
    )

    check(realized["conflict"] > 0, "conflict control injected nothing")

    values = {}

    for strategy in v5.STRATEGIES:
        result, recovery_meta = v5.execute_once(
            work,
            oracle,
            strategy,
            False,
        )

        metrics = v5.compute_metrics(
            result,
            oracle,
            realized,
            recovery_meta,
        )

        values[strategy] = metrics["state_correctness_rate"]

    check(
        values["S2_temporal"] > values["S1_minimal"],
        "conflict fixture does not distinguish temporal processing",
    )
    check(
        values["S4_full"] > values["S3_recovery"],
        "conflict fixture does not distinguish temporal processing for S4/S3",
    )


def test_metric_arithmetic_and_bounds():
    canonical = v5.canonical_dataset(1_000, 1301)
    oracle = v5.build_oracle(canonical)

    work, realized = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        0.05,
        0.05,
        0.05,
        0.05,
    )

    for strategy in v5.STRATEGIES:
        result, recovery_meta = v5.execute_once(
            work,
            oracle,
            strategy,
            True,
        )

        m = v5.compute_metrics(
            result,
            oracle,
            realized,
            recovery_meta,
        )

        pairs = (
            (
                "state_correctness_rate",
                "entities_matching_oracle",
                "oracle_entities",
            ),
            (
                "duplicate_leakage_rate",
                "duplicate_leakage_count",
                "duplicate_denominator",
            ),
            (
                "invalid_key_leakage_rate",
                "invalid_key_leakage_count",
                "invalid_key_denominator",
            ),
            (
                "stale_state_rate",
                "stale_state_count",
                "stale_state_denominator",
            ),
            (
                "recovery_completeness_rate",
                "recovered_expected_count",
                "recovery_denominator",
            ),
            (
                "false_rejection_rate",
                "false_rejection_count",
                "false_rejection_denominator",
            ),
            (
                "recovery_duplicate_effect_rate",
                "recovery_duplicate_effect_count",
                "recovery_duplicate_effect_denominator",
            ),
        )

        for rate, numerator, denominator in pairs:
            check(m[denominator] > 0, f"{strategy}: {denominator} <= 0")

            expected = m[numerator] / m[denominator]

            check(
                abs(m[rate] - expected) < 1e-12,
                f"{strategy}: arithmetic mismatch for {rate}",
            )

            check(
                0.0 <= m[rate] <= 1.0,
                f"{strategy}: {rate} outside [0,1]",
            )


def test_expected_matrix_counts_without_execution():
    principal = (
        len(v5.SIZES)
        * len(v5.SEEDS)
        * len(v5.INTENSITIES)
        * len(v5.STRATEGIES)
    )

    controls = (
        len(v5.SIZES)
        * len(v5.SEEDS)
        * len(v5.CONTROL_FAULTS)
        * len(v5.STRATEGIES)
    )

    check(principal == 180, "principal matrix must contain 180 observations")
    check(controls == 300, "control matrix must contain 300 observations")
    check(principal + controls == 480, "total matrix must equal 480")


def test_reproducibility_metadata_shape():
    canonical = v5.canonical_dataset(100, 1301)
    oracle = v5.build_oracle(canonical)

    work, realized = v5.inject_non_recovery_faults(
        canonical,
        oracle,
        1301,
        duplicate_rate=0.05,
        null_rate=0,
        late_rate=0,
        conflict_rate=0,
    )

    old_repeats = v5.REPEATS

    try:
        v5.REPEATS = 1

        row = v5.build_observation(
            experiment_kind="test",
            fault_condition="duplicate",
            dataset_size=100,
            seed=1301,
            intensity=0.05,
            strategy="S1_minimal",
            canonical=canonical,
            oracle=oracle,
            work=work,
            realized=realized,
            recovery_enabled=False,
            commit_sha="TEST-SHA",
        )
    finally:
        v5.REPEATS = old_repeats

    required = {
        "schema_version",
        "experiment_kind",
        "fault_condition",
        "dataset_size",
        "seed",
        "nominal_intensity",
        "checkpoint_fraction",
        "replay_fraction",
        "strategy",
        "realized_duplicate",
        "realized_null_key",
        "realized_late",
        "realized_conflict_entities",
        "recovery_replay_count",
        "already_committed_replay_count",
        "recovery_replays_suppressed",
        "recovery_replays_reprocessed",
        "recovery_duplicate_effect_count",
        "recovery_duplicate_effect_rate",
        "runtime_ms_median",
        "runtime_ms_mean",
        "timing_repeats",
        "commit_sha",
        "python",
    }

    missing = required - set(row)

    check(not missing, f"missing reproducibility fields: {sorted(missing)}")


def run_all():
    tests = [
        test_frozen_constants,
        test_strategy_definitions,
        test_canonical_determinism,
        test_oracle_independence,
        test_fault_injection_determinism,
        test_conflict_entity_semantics,
        test_committed_before_replay,
        test_recovery_identifiability,
        test_duplicate_control,
        test_null_control,
        test_late_control_temporal_distinction,
        test_conflict_control_temporal_distinction,
        test_metric_arithmetic_and_bounds,
        test_expected_matrix_counts_without_execution,
        test_reproducibility_metadata_shape,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print()
    print("Experiment Suite V5 pre-result tests: PASS")
    print(
        "Validated: frozen constants, strategy definitions, independent oracle, "
        "deterministic injection, entity-level conflict semantics, all five "
        "control classes, committed-before-replay recovery, recovery "
        "identifiability, metric arithmetic/bounds, matrix counts, and "
        "reproducibility metadata."
    )


if __name__ == "__main__":
    run_all()