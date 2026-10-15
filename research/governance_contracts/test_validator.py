import copy
import unittest
from validator import fixture, validate

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.expected = fixture()

    def test_identical(self):
        self.assertTrue(validate(self.expected, copy.deepcopy(self.expected))["passed"])

    def test_row_order_does_not_matter(self):
        actual = copy.deepcopy(self.expected)
        actual["rows"].reverse()
        self.assertTrue(validate(self.expected, actual)["passed"])

    def test_duplicate_row_detected(self):
        actual = copy.deepcopy(self.expected)
        actual["rows"].append(actual["rows"][0])
        self.assertFalse(validate(self.expected, actual)["checks"]["data"])

    def test_schema_change_detected(self):
        actual = copy.deepcopy(self.expected)
        actual["schema"][0]["type"] = "STRING"
        self.assertFalse(validate(self.expected, actual)["checks"]["schema"])

    def test_governance_loss_detected_even_if_rows_match(self):
        actual = copy.deepcopy(self.expected)
        actual["governance"]["email"]["data_policies"] = []
        result = validate(self.expected, actual)
        self.assertTrue(result["checks"]["data"])
        self.assertFalse(result["checks"]["governance"])
        self.assertFalse(result["passed"])

    def test_missing_section_fails_closed(self):
        actual = copy.deepcopy(self.expected)
        del actual["governance"]
        self.assertFalse(validate(self.expected, actual)["passed"])

    def test_inputs_unchanged(self):
        actual = copy.deepcopy(self.expected)
        before = copy.deepcopy(actual)
        validate(self.expected, actual)
        self.assertEqual(before, actual)

if __name__ == "__main__":
    unittest.main()
