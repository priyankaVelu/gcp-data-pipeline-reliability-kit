import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from fractions import Fraction as F
from research.queryguard.bundle_v1 import experiment, verify

class BundleArtifacts(unittest.TestCase):
    def test_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            out=Path(tmp)/'run'
            data=experiment.run(out,phases=(('test',(7,),(4,)),),densities=(F(1,5),),fractions=(F(1,2),))
            self.assertEqual(len(data['rows']),12)
            verify.verify(out)
            with self.assertRaises(FileExistsError): experiment.run(out)
            path=out/'results.csv';path.write_text(path.read_text()+'corrupt')
            with self.assertRaises(AssertionError):verify.verify(out)
