import unittest
from research.run_paper_experiments_v3 import base,run,REPEATS
class V3Tests(unittest.TestCase):
    def test_deterministic_base(self):self.assertEqual(base(100,1301),base(100,1301))
    def test_matrix_per_configuration(self):
        r=run(100,1301,.05,"test");self.assertEqual(len(r),11);self.assertEqual({x["timing_repeats"] for x in r},{REPEATS})
    def test_controlled_invariants(self):
        r=run(100,1301,.05,"test")
        good={"dedup_then_validate","event_time_order","event_time_latest_write","idempotent_replay"}
        self.assertTrue(all(x["correct"]==1 for x in r if x["strategy"] in good))
    def test_failure_comparators(self):
        r=run(100,1301,.05,"test")
        bad={"arrival_order","arrival_last_write","append_replay"}
        self.assertTrue(all(x["correct"]==0 for x in r if x["strategy"] in bad))
if __name__=="__main__":unittest.main()
