"""Unit tests for the synthetic first milestone."""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "proof_of_concept.py"
spec = importlib.util.spec_from_file_location("queryguard_poc", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class QueryGuardProofTests(unittest.TestCase):
    def test_shared_scan_cost(self):
        self.assertEqual(module.plan_cost(module.CHECKS[:2]), 7)
        self.assertEqual(module.plan_cost((module.CHECKS[0],)), 6)
        self.assertEqual(module.plan_cost((module.CHECKS[0], module.CHECKS[2])), 12)

    def test_coverage_optimum(self):
        self.assertEqual(module.summary(module.optimize("coverage"))["checks"], ["C"])

    def test_risk_optimum(self):
        self.assertEqual(module.summary(module.optimize("risk_reduction"))["checks"], ["A", "B"])

    def test_budget_respected(self):
        for plan in module.feasible_plans():
            self.assertLessEqual(module.plan_cost(plan), module.BUDGET)

    def test_invalid_objective(self):
        with self.assertRaises(ValueError):
            module.optimize("invalid")

    def test_negative_budget(self):
        with self.assertRaises(ValueError):
            module.feasible_plans(budget=-1)


if __name__ == "__main__":
    unittest.main()
