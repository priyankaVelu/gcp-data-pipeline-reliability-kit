"""Offline synthetic recovery contract validator. No GCP integration."""
import json
from collections import Counter

def validate(expected, observed):
    violations = []
    for section in ("rows", "schema", "governance"):
        if section not in expected or section not in observed:
            violations.append({"dimension": section, "code": "MISSING_SECTION"})
    if violations:
        return {"passed": False, "checks": {}, "violations": violations}
    def signature(row):
        return json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False)
    checks = {
        "data": Counter(map(signature, expected["rows"])) == Counter(map(signature, observed["rows"])),
        "schema": expected["schema"] == observed["schema"],
        "governance": expected["governance"] == observed["governance"],
    }
    for dimension, ok in checks.items():
        if not ok:
            violations.append({"dimension": dimension, "code": "CONTRACT_MISMATCH"})
    return {"passed": all(checks.values()), "checks": checks, "violations": violations}

def fixture():
    return {
        "rows": [{"id": 1, "email": "synthetic@example.invalid"}, {"id": 2, "email": None}],
        "schema": [{"name": "id", "type": "INT64", "mode": "REQUIRED"}, {"name": "email", "type": "STRING", "mode": "NULLABLE"}],
        "governance": {"email": {"data_policies": ["synthetic-mask-policy"], "governance_tags": ["synthetic-sensitive-tag"]}, "row_access_policies": []},
    }

if __name__ == "__main__":
    reference = fixture()
    print(json.dumps({"experiment": "governance_aware_recovery_v1", "mode": "synthetic", "result": validate(reference, fixture())}, indent=2))
