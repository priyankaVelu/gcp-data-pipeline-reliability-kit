import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

verify=load('cdc_verify','research/cdc_lab/v2/verify.py')
runner=load('cdc_v2_run','research/cdc_lab/v2/run.py')


class ArtifactTests(unittest.TestCase):
    def test_original_integrity_and_counts(self):
        root=Path(__file__).resolve().parents[1]
        data=verify.verify(root/'research/cdc_lab/results/run-1')
        self.assertEqual((len(data['principal']),len(data['bounded'])),(126,36))
        self.assertEqual(verify.preserve(root)['status'],'preserved')

    def test_scoring_of_invalid_and_valid_controls(self):
        self.assertEqual(len(runner.SCENARIOS)*len(runner.SIZES)*len(runner.SEEDS)*3,144)
        for name in ('conflicting_id','same_version_conflict'):
            row=runner.observe(8,7,name,'version')
            self.assertTrue(row['input_rejected'])
            self.assertIsNone(row['state_correct'])
        row=runner.observe(8,7,'duplicate_only','arrival')
        self.assertTrue(row['state_correct'])
        self.assertEqual(len(row['runtime_samples_ms']),5)
        self.assertGreater(row['counters']['restart']['applied'],16)

    def test_fresh_probe_order_isolation(self):
        for capacity in (0,4,16,None):
            first=runner.expiry('version',capacity,7,'conflict_first')
            second=runner.expiry('version',capacity,7,'exact_then_conflict')
            self.assertEqual(first['conflict_detected'],capacity is None)
            self.assertEqual(second['conflict_detected'],capacity != 0)
            self.assertTrue(first['final_state_unchanged'])
            self.assertTrue(second['final_state_unchanged'])

    def test_hash_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)
            (p/'SHA256.json').write_text(json.dumps(dict.fromkeys(('results.json','principal.csv','bounded.csv'),'bad')))
            for name in ('results.json','principal.csv','bounded.csv'):(p/name).write_text('corrupted')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                verify.verify(p)
