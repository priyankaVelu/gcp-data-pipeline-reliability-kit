import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('cdc_lab', Path(__file__).resolve().parents[1]/'research/cdc_lab/run.py')
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


class CdcLabTests(unittest.TestCase):
    def test_determinism_and_oracle_independence(self):
        base = lab.canonical(8)
        expected = copy.deepcopy(lab.oracle(base))
        a = lab.workload(base, 'out_of_order', 7)
        self.assertEqual(a, lab.workload(base, 'out_of_order', 7))
        a[0]['value'] = 'mutated'
        self.assertEqual(expected, lab.oracle(base))
        self.assertEqual(expected['k0'], dict(version=4, value='value-4', deleted=False))

    def test_counterexample_and_tombstones(self):
        base = [e for e in lab.canonical(1) if e['version'] in (3,4)]
        events = list(reversed(base))
        expected = lab.oracle(base)
        for strategy in ('arrival', 'id_only'):
            self.assertNotEqual(lab.process(events, strategy)['state'], expected)
        self.assertEqual(lab.process(events, 'version')['state'], expected)
        self.assertFalse(lab.process(events, 'id_only')['nondecreasing_version'])

    def test_all_valid_scenarios_recovery_and_inputs(self):
        base = lab.canonical(8)
        original = copy.deepcopy(base)
        for seed in lab.SEEDS:
            for scenario in lab.SCENARIOS:
                events = lab.workload(base, scenario, seed)
                if scenario == 'conflicts':
                    for strategy in lab.STRATEGIES:
                        with self.assertRaises(lab.InvalidEvent):
                            lab.process(events, strategy)
                    continue
                output = lab.process(events, 'version', 2, 7, True)
                self.assertEqual(output['state'], lab.oracle(base))
                self.assertTrue(output['redelivery_state_unchanged'])
                self.assertTrue(output['nondecreasing_version'])
                self.assertEqual(output['lost_attempts'], 5)
        self.assertEqual(base, original)

    def test_fifo_capacity_and_online_conflict_limit(self):
        for cap in (0,4,16):
            result = lab.bounded('version', cap, 7)
            self.assertLessEqual(result['ledger_peak'], cap)
            self.assertFalse(result['duplicate_recognized'])
            self.assertFalse(result['redelivery_changed_state'])
            # Exact stale replay refreshes an evicted identity before conflict probe.
            self.assertEqual(result['conflict_detected'], cap > 0)
        result = lab.bounded('version', None, 7)
        self.assertTrue(result['duplicate_recognized'])
        self.assertTrue(result['conflict_detected'])

    def test_checkpoint_independence_and_boundaries(self):
        p = lab.Processor('version')
        saved = p.checkpoint()
        p.apply(lab.canonical(1)[0])
        p.restore(saved)
        self.assertEqual(p.state, {})
        for cut in (0,1,4):
            for cp in (0,cut):
                self.assertEqual(lab.process(lab.canonical(1),'version',cp,cut)['state'],lab.oracle(lab.canonical(1)))
        with self.assertRaises(ValueError):
            lab.process([], 'version', 1, 0)
