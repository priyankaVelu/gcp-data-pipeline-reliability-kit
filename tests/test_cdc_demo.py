import copy
import itertools
import json
import subprocess
import sys
import unittest
from pipeline_reliability.cdc_demo import InvalidEvent, demonstrate, oracle, replay, scenario, naive


def event(eid, key, version, value, deleted=False):
    return {"event_id": eid, "key": key, "version": version, "value": value, "deleted": deleted}


class CdcDemoTests(unittest.TestCase):
    def test_seeded_restart_boundaries_and_idempotency(self):
        for seed in range(20):
            events = scenario(seed)
            for cut in (0, 1, 5, len(events) - 1, len(events)):
                for checkpoint in (0, cut // 2, cut):
                    actual, _, details, inv, _ = replay(events, cut, checkpoint)
                    self.assertEqual(actual, oracle(events))
                    self.assertTrue(all(inv.values()), (seed, cut, checkpoint, inv))
                    self.assertEqual(details[0]["replayed_after_restart"], cut - checkpoint)

    def test_conflicts_all_permutations_oracle_and_replay(self):
        cases = [
            [event("a", "x", 2, "left"), event("b", "x", 2, "right")],
            [event("a", "x", 2, "left"), event("a", "x", 2, "right")],
            [event("a", "x", 1, "left"), event("a", "y", 1, "left")],
        ]
        for case in cases:
            for permutation in itertools.permutations(case):
                with self.assertRaises(InvalidEvent):
                    oracle(list(permutation))
                with self.assertRaises(InvalidEvent):
                    replay(list(permutation))

    def test_delete_reinsert_and_stale_delete(self):
        events = [event("a", "x", 1, "first"), event("c", "x", 3, "again"),
                  event("b", "x", 2, "gone", True)]
        for permutation in itertools.permutations(events):
            state, _, _, inv, _ = replay(list(permutation), 2, 1)
            self.assertEqual(state["x"], {"version": 3, "value": "again", "deleted": False})
            self.assertTrue(all(inv.values()))

    def test_invalid_inputs(self):
        valid = event("a", "x", 1, "ok")
        for bad in [dict(valid, version=True), dict(valid, version=0),
                    dict(valid, deleted="false"), dict(valid, event_id=""),
                    dict(valid, value=None), dict(valid, extra=1)]:
            with self.assertRaises(InvalidEvent):
                oracle([bad])
        for cp, cut in [(3, 2), (-1, 2), (0, 100)]:
            with self.assertRaises(ValueError):
                replay([valid], cut, cp)

    def test_baseline_failure_and_json(self):
        events = [event("a", "x", 2, "new"), event("b", "x", 1, "old")]
        self.assertNotEqual(naive(events, 2, 0), oracle(events))
        result = demonstrate()
        self.assertEqual(result["result"]["oracle"]["verdict"], "pass")
        self.assertIn("baseline_wrong_keys", result["result"])
        self.assertIn("recovery", result["result"])
        proc = subprocess.run([sys.executable, "-m", "pipeline_reliability.cdc_demo",
                               "--seed", "7", "--checkpoint-after", "2", "--interrupt-after", "5"],
                              capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["result"]["passed"])
        bad = subprocess.run([sys.executable, "-m", "pipeline_reliability.cdc_demo",
                              "--checkpoint-after", "9", "--interrupt-after", "3"],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["status"], "error")
