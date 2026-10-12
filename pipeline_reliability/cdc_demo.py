"""Synthetic CDC replay correctness lab. No durable storage or exactly-once claim."""
import argparse
import copy
import json
import random


class InvalidEvent(ValueError):
    pass


def validate(events):
    if not isinstance(events, list):
        raise InvalidEvent("events must be a list")
    ids, versions = {}, {}
    for i, e in enumerate(events):
        if not isinstance(e, dict) or set(e) != {"event_id", "key", "version", "value", "deleted"}:
            raise InvalidEvent(f"invalid fields at event {i}")
        if not isinstance(e["event_id"], str) or not e["event_id"] or not isinstance(e["key"], str) or not e["key"]:
            raise InvalidEvent(f"empty or invalid identity at event {i}")
        if type(e["version"]) is not int or e["version"] < 1 or type(e["deleted"]) is not bool:
            raise InvalidEvent(f"invalid version/deleted at event {i}")
        if not isinstance(e["value"], str):
            raise InvalidEvent(f"invalid value at event {i}")
        payload = (e["key"], e["version"], e["value"], e["deleted"])
        if e["event_id"] in ids and ids[e["event_id"]] != payload:
            raise InvalidEvent(f"conflicting payload for event_id {e['event_id']}")
        ids[e["event_id"]] = payload
        kv = (e["key"], e["version"])
        if kv in versions and versions[kv] != (e["value"], e["deleted"]):
            raise InvalidEvent(f"conflicting same-key/same-version event {kv}")
        versions[kv] = (e["value"], e["deleted"])


def scenario(seed=7):
    rng = random.Random(seed)
    events = [{"event_id": f"{key}-{version}", "key": key, "version": version,
               "value": f"{key}-v{version}", "deleted": key == "gamma" and version == 3}
              for key in ("alpha", "beta", "gamma") for version in range(1, 5)]
    events.extend(copy.deepcopy(e) for e in events[::3])
    rng.shuffle(events)
    return events


def oracle(events):
    """Independent order-free set reduction with whole-stream conflict detection."""
    validate(events)
    keys = sorted({e["key"] for e in events})
    return {key: {"version": max(e["version"] for e in events if e["key"] == key),
                  "value": next(e["value"] for e in events if e["key"] == key and
                                e["version"] == max(x["version"] for x in events if x["key"] == key)),
                  "deleted": next(e["deleted"] for e in events if e["key"] == key and
                                  e["version"] == max(x["version"] for x in events if x["key"] == key))}
            for key in keys}


def blank():
    return {"state": {}, "seen": {}}


def apply(snapshot, event):
    eid = event["event_id"]
    payload = [event[k] for k in ("key", "version", "value", "deleted")]
    if eid in snapshot["seen"]:
        if snapshot["seen"][eid] != payload:
            raise InvalidEvent("conflicting event ID")
        return "duplicate"
    snapshot["seen"][eid] = payload
    key = event["key"]
    old = snapshot["state"].get(key)
    if old is not None and event["version"] < old["version"]:
        return "stale"
    if old is not None and event["version"] == old["version"] and (
        old["value"] != event["value"] or old["deleted"] != event["deleted"]):
        raise InvalidEvent("conflicting version")
    snapshot["state"][key] = {k: event[k] for k in ("version", "value", "deleted")}
    return "applied"


def replay(events, interrupt_after=None, checkpoint_after=0, redeliver=True):
    validate(events)
    n = len(events)
    if interrupt_after is None:
        interrupt_after = n
    if type(interrupt_after) is not int or type(checkpoint_after) is not int or not (0 <= checkpoint_after <= interrupt_after <= n):
        raise ValueError("require 0 <= checkpoint_after <= interrupt_after <= event count")
    working = blank()
    counters = {"applied": 0, "duplicate": 0, "stale": 0}
    committed = copy.deepcopy(working)
    for i in range(interrupt_after):
        counters[apply(working, events[i])] += 1
        if i + 1 == checkpoint_after:
            committed = copy.deepcopy(working)
    # Serialize/deserialize the logical snapshot to model persistence across a new process.
    # No file, fsync, atomic commit or crash durability is provided.
    restored = json.loads(json.dumps(committed))
    recovery = {"checkpoint_offset": checkpoint_after,
                "interruption_offset": interrupt_after,
                "uncommitted_events_lost": interrupt_after - checkpoint_after,
                "replayed_after_restart": interrupt_after - checkpoint_after,
                "redelivered_after_recovery": 0,
                "persistence": "simulated serialized logical checkpoint (not durable storage)"}
    recovery_counts = {"applied": 0, "duplicate": 0, "stale": 0}
    for e in events[checkpoint_after:]:
        recovery_counts[apply(restored, e)] += 1
    before = copy.deepcopy(restored)
    if redeliver:
        for e in events:
            recovery_counts[apply(restored, e)] += 1
            recovery["redelivered_after_recovery"] += 1
    invariants = {"state_matches_oracle": restored["state"] == oracle(events),
                  "redelivery_idempotent": restored == before,
                  "dedup_ledger_complete": len(restored["seen"]) == len({e["event_id"] for e in events}),
                  "checkpoint_is_earlier": checkpoint_after <= interrupt_after,
                  "replayed_uncommitted_suffix": recovery["replayed_after_restart"] == interrupt_after - checkpoint_after}
    return restored["state"], counters, [recovery], invariants, recovery_counts


def naive(events, interrupt_after, checkpoint_after):
    """Intentionally incorrect: last arrival wins, no version guard or dedup ledger."""
    state = {}
    for e in events[:checkpoint_after]:
        state[e["key"]] = {k: e[k] for k in ("version", "value", "deleted")}
    for e in events[checkpoint_after:]:
        state[e["key"]] = {k: e[k] for k in ("version", "value", "deleted")}
    return state


def demonstrate(seed=7, interrupt_after=5, checkpoint_after=2):
    events = scenario(seed)
    expected = oracle(events)
    actual, _, recovery, invariants, counts = replay(events, interrupt_after, checkpoint_after)
    baseline = naive(events, interrupt_after, checkpoint_after)
    baseline_wrong_keys = sorted(k for k in expected if baseline.get(k) != expected[k])
    passed = all(invariants.values())
    return {"schema_version": "2.0", "command": "cdc-replay-demo",
            "status": "pass" if passed else "fail",
            "result": {"passed": passed, "seed": seed, "events": len(events),
                       "corrected_state": actual, "baseline_state": baseline,
                       "baseline_wrong_keys": baseline_wrong_keys,
                       "oracle": {"verdict": "pass" if actual == expected else "fail", "state": expected},
                       "recovery": recovery[0], "recovery_counts": counts, "invariants": invariants,
                       "baseline_demonstrates_failure": bool(baseline_wrong_keys)}}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Synthetic CDC recovery correctness lab")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--interrupt-after", type=int, default=5)
    parser.add_argument("--checkpoint-after", type=int, default=2)
    args = parser.parse_args(argv)
    try:
        result = demonstrate(args.seed, args.interrupt_after, args.checkpoint_after)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["result"]["passed"] else 1
    except (ValueError, InvalidEvent) as exc:
        print(json.dumps({"schema_version": "2.0", "status": "error", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
