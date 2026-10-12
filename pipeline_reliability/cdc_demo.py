"""Deterministic CDC replay demonstration; standard library only."""
import argparse
import json
import random
from collections import defaultdict


def scenario(seed=7):
    rng = random.Random(seed)
    events = []
    for key in ("alpha", "beta", "gamma"):
        for version in range(1, 5):
            events.append({"event_id": f"{key}-{version}", "key": key,
                           "version": version, "value": f"{key}-v{version}",
                           "deleted": key == "gamma" and version == 4})
    events.extend(dict(e) for e in events[::3])
    rng.shuffle(events)
    return events


def oracle(events):
    """Independent batch reduction, not the replay algorithm."""
    by_key = defaultdict(list)
    for event in events:
        by_key[event["key"]].append(event)
    return {key: {"version": max(rows, key=lambda x: x["version"])["version"],
                  "value": max(rows, key=lambda x: x["version"])["value"],
                  "deleted": max(rows, key=lambda x: x["version"])["deleted"]}
            for key, rows in sorted(by_key.items())}


def replay(events, interrupt_after=None):
    state, seen = {}, set()
    duplicates = stale = 0
    checkpoints = []
    for index, event in enumerate(events):
        if interrupt_after is not None and index == interrupt_after:
            checkpoints.append({"processed": index, "state": dict(state), "seen": sorted(seen)})
            # Simulate restart: state and dedup ledger are restored from durable checkpoint.
            state, seen = dict(checkpoints[-1]["state"]), set(checkpoints[-1]["seen"])
        eid, key = event["event_id"], event["key"]
        if eid in seen:
            duplicates += 1
            continue
        seen.add(eid)
        current = state.get(key)
        if current and event["version"] < current["version"]:
            stale += 1
            continue
        if current and event["version"] == current["version"] and (
            event["value"], event["deleted"]) != (current["value"], current["deleted"]):
            raise ValueError("conflicting events at same key/version")
        state[key] = {k: event[k] for k in ("version", "value", "deleted")}
    return state, duplicates, stale, checkpoints


def demonstrate(seed=7, interrupt_after=5):
    events = scenario(seed)
    expected = oracle(events)
    actual, duplicates, stale, checkpoints = replay(events, interrupt_after)
    second, _, _, _ = replay(events + events, interrupt_after)
    passed = actual == expected == second
    return {"schema_version": "1.0", "command": "cdc-replay-demo",
            "status": "pass" if passed else "fail",
            "result": {"passed": passed, "seed": seed, "events": len(events),
                       "duplicates_ignored": duplicates, "stale_events_ignored": stale,
                       "interruption_at": interrupt_after, "checkpoints": checkpoints,
                       "actual_state": actual, "oracle_state": expected,
                       "idempotent_full_replay": actual == second}}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Synthetic CDC replay correctness demo")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--interrupt-after", type=int, default=5)
    args = parser.parse_args(argv)
    if args.interrupt_after < 0:
        parser.error("--interrupt-after must be nonnegative")
    result = demonstrate(args.seed, args.interrupt_after)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
