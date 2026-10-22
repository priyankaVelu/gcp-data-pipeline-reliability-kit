from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.queryguard.overlap_v1 import experiment, verify, fixtures


class ExperimentTests(unittest.TestCase):
    def run_small(self,path):
        with redirect_stdout(io.StringIO()):
            return experiment.run(path,seeds=(7,),sizes=(4,),densities=(Fraction(1,5),),budget_fractions=(Fraction(1,2),))

    def test_roundtrip_new_path_and_independent_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'run'
            data=self.run_small(output)
            result=verify.verify(output)
            self.assertEqual((result['rows'],result['instances'],result['independently_checked_optima']),(4,1,1))
            self.assertEqual(data['metadata']['repeats'],3)
            with self.assertRaises(FileExistsError):self.run_small(output)

    def test_repeatable_inputs_selections_and_non_timing_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            a=self.run_small(Path(directory)/'a');b=self.run_small(Path(directory)/'b')
            strip=lambda data:[{k:v for k,v in r.items() if k not in ('runtime_ms','runtime_samples_ms')} for r in data['rows']]
            self.assertEqual(strip(a),strip(b))

    def test_failure_preserved_not_zero_row(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'bad'
            with patch.object(experiment.planner,'solve',side_effect=RuntimeError('injected technical failure')):
                with self.assertRaises(RuntimeError):self.run_small(output)
            failure=json.loads((output/'failure.json').read_text())
            self.assertIn('injected technical failure',failure['error'])
            self.assertFalse((output/'results.json').exists())

    def test_hash_corruption_and_rehashed_accounting_corruption(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'run';self.run_small(output)
            original=(output/'results.json').read_bytes()
            (output/'results.json').write_text('bad')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):verify.verify(output)
            (output/'results.json').write_bytes(original)
            data=json.loads(original);data['rows'][0]['risk_reduction']='999999'
            (output/'results.json').write_text(json.dumps(data))
            hashes=json.loads((output/'SHA256.json').read_text())
            hashes['results.json']=hashlib.sha256((output/'results.json').read_bytes()).hexdigest()
            (output/'SHA256.json').write_text(json.dumps(hashes))
            with self.assertRaises(ValueError):verify.verify(output)

    def test_zero_optimum_ratio_is_explicitly_undefined(self):
        problem=fixtures.generated(7,0)
        row=experiment.row(problem,0,'exact')
        self.assertEqual(row['risk_reduction'],'0')
        record=dict(row,optimality_ratio=None,risk_gap='0')
        rows=[dict(record,policy=policy) for policy in experiment.planner.POLICIES]
        summary=experiment.summary(rows)
        self.assertEqual(summary['exact']['undefined_ratios'],1)
        self.assertIsNone(summary['exact']['median_optimality_ratio'])

    def test_invalid_generator_inputs(self):
        for args in ((True,4,.2),(7,-1,.2),(7,4,2),(7,4,float('nan'))):
            with self.assertRaises(ValueError):fixtures.generated(*args)
