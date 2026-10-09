"""Focused regression checks for the DSN validity amendment.

Run: python research/test_dsn2027_validity.py
"""
import importlib.util
import sys
from pathlib import Path

path = Path(__file__).with_name("run_paper_experiments_v4.py")
spec = importlib.util.spec_from_file_location("dsn_v4", path)
v4 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = v4
spec.loader.exec_module(v4)

rows = v4.canonical(1000, 1301)
work, realized = v4.inject(
    rows, 1301, duplicate_rate=.05, null_key_rate=.05,
    late_rate=.05, conflict_rate=.05, recovery=True
)
replay_count = realized["recovery_replay"]
assert replay_count > 0
assert all("recovery_replay" in x["fault_tags"] for x in work[-replay_count:])
assert all("recovery_replay" not in x["fault_tags"] for x in work[:-replay_count])
for strategy in v4.STRATEGIES:
    _, _, detected = v4.process(work, strategy)
    assert detected["late"] == 0, "Temporal handling is not an alert"
    assert detected["conflict"] == 0, "Conflict resolution is not an alert"
print("DSN focused amendment regression checks: PASS")
print("NOTE: These tests do not validate checkpoint semantics or the correctness oracle.")
