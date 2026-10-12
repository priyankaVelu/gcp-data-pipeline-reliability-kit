import unittest
from pipeline_reliability.cdc_demo import demonstrate, replay, oracle, scenario


class CdcDemoTests(unittest.TestCase):
    def test_seeded_scenarios(self):
        for seed in range(25):
            for cut in (0, 1, 5, 12, 16):
                self.assertTrue(demonstrate(seed, cut)["result"]["passed"])

    def test_duplicate_and_out_of_order(self):
        events = scenario(3)
        self.assertEqual(replay(events)[0], oracle(events))
        self.assertEqual(replay(events + events)[0], oracle(events))

    def test_conflicting_version_rejected(self):
        with self.assertRaises(ValueError):
            replay([{"event_id": "a", "key": "x", "version": 1, "value": "a", "deleted": False},
                    {"event_id": "b", "key": "x", "version": 1, "value": "b", "deleted": False}])
