import unittest
from research.run_paper_experiments import make_events, inject_duplicate_faults, inject_null_key_faults, run_config, summarize

class PaperExperimentTests(unittest.TestCase):
    def test_generation_is_deterministic(self):
        self.assertEqual(make_events(20,101),make_events(20,101))

    def test_fault_injection_counts(self):
        rows=make_events(100,101)
        dup,k=inject_duplicate_faults(rows,.1,102)
        self.assertEqual((len(dup)-len(rows),k),(10,10))
        nulls,k=inject_null_key_faults(rows,.1,103)
        self.assertEqual(sum(x["customer_id"] is None for x in nulls),k)

    def test_controlled_invariants_hold(self):
        rows=run_config(100,101,.1,"test")
        controlled=[x for x in rows if x["variant"]=="controlled"]
        self.assertEqual(len(controlled),4)
        self.assertTrue(all(x["correct"]==1 for x in controlled))

    def test_summary_is_complete(self):
        rows=run_config(100,101,.1,"test")
        s=summarize(rows)
        self.assertEqual(len(s),8)
        self.assertEqual({x["scenario"] for x in s},{"duplicate_replay","null_business_key","bounded_backfill","stale_data"})

if __name__=="__main__": unittest.main()
