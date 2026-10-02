import unittest
from research.run_paper_experiments_v2 import data,duplicate,nulls,run,summary,REPEATS

class PaperExperimentV2Tests(unittest.TestCase):
    def test_deterministic_data(self):
        self.assertEqual(data(50,1103),data(50,1103))
    def test_fault_rates(self):
        rows=data(1000,1103);d,k=duplicate(rows,.05,1120);self.assertEqual((len(d)-1000,k),(50,50))
        n,k=nulls(rows,.1,1132);self.assertEqual(sum(x["customer_id"] is None for x in n),100)
    def test_scenarios_and_comparators(self):
        r=run(100,1103,.01,"test");self.assertEqual(len(r),8)
        self.assertEqual({x["scenario"] for x in r},{"duplicate_replay","null_business_key","partial_recovery","bounded_recovery"})
        self.assertEqual({x["timing_repeats"] for x in r},{REPEATS})
    def test_expected_correctness_pattern(self):
        r=run(100,1103,.01,"test")
        by={(x["scenario"],x["strategy"]):x for x in r}
        self.assertEqual(by[("partial_recovery","append_replay_comparator")]["correct"],0)
        self.assertEqual(by[("partial_recovery","idempotent_replay_control")]["correct"],1)
        self.assertTrue(all(x["correct"]==1 for x in r if x["scenario"]!="partial_recovery"))
    def test_summary(self):
        self.assertEqual(len(summary(run(100,1103,.01,"test"))),8)
if __name__=="__main__":unittest.main()
