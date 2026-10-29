# Bounded bundle planning (synthetic research)

This version leaves overlap_v1 and Papers 1/2 unchanged. Read [PROTOCOL.md](PROTOCOL.md)
for the design committed before measurements, and [RESULTS.md](RESULTS.md) for actual
positive, neutral and negative outcomes. It is a fixed-charge weighted coverage
lookahead heuristic; no novelty or approximation guarantee is asserted.

From the repository root, Python 3.10+ with no third-party dependencies:

```sh
python -m unittest discover -s research/queryguard/tests -v
python -m research.queryguard.bundle_v1 --fixture triple_trap --budget 8 --k 2
python -m research.queryguard.bundle_v1 --fixture triple_trap --budget 8 --k 3
python -m research.queryguard.bundle_v1 --fixture shared_scan_trap --budget 7 --k 2 --cost-model no_sharing
python -m research.queryguard.bundle_v1.experiment --output /tmp/queryguard-bundle-new-run
python -m research.queryguard.bundle_v1.verify /tmp/queryguard-bundle-new-run
python -m research.queryguard.bundle_v1.report /tmp/queryguard-bundle-new-run
python -m research.queryguard.bundle_v1.verify research/queryguard/bundle_v1/results/run-1
```

Output directories must be new. The full experiment makes 1,080 policy observations
(three timed executions each), plus 36 fixture observations, over 30 deterministic
base instances. It independently enumerates 180 optima up to 14 checks. Verification
re-enumerates those optima; this can take minutes. CSV and JSON include all policies
under the same numeric budgets. No-sharing clones setup costs per check without
changing singleton costs, incidence or source budgets. Differences across cost modes
include changed feasible sets; use each mode’s own exact optimum.

The bundle planner enumerates sizes 1..k at every round, for k=2 or 3, and scores
newly covered scenario/consumer atoms once. Unopened scan groups are charged once
per union, plus each check’s evaluation cost. Free positive gains rank first; then
risk/cost, gain, lower cost, smaller bundle, lexicographic IDs. k=1 is a diagnostic
that matches risk-aware greedy. Returned step witnesses expose marginal risk/cost.
The conservative bound is O(n * sum(C(n,j),j=1..k) * (k+a+g)). Increasing k need not
improve the final plan. There is no fallback to a better singleton solution.

The triple trap takes well under one minute: shared A/B/C each protect loss 8 and
share setup 5 plus evaluation 1; D protects 15 at cost 6. Budget 8. Pair lookahead
chooses D (15), triple lookahead chooses ABC (24). Coverage and cost-aware greedy
also find ABC: this is not evidence of unique superiority. In no-sharing mode ABC
is infeasible and exact selects D. The overlap fixture demonstrates that repeated
incidence does not earn repeated risk credit.

`results/run-1` is immutable measured evidence. Its metadata identifies the measured
commit, source/protocol SHA-256 hashes, Python/platform and clean tracked state.
`PRESERVATION.json` locks every pre-existing tracked file, including historical
input/result hashes. `execution.json` distinguishes end-to-end measurement time
(including oracle work) from solver-only samples. Reporting code and documentation
were added after measurement; reproduce the algorithms using the recorded source
hashes. No real query execution, cloud billing, calibrated incident probabilities,
detection uncertainty, remediation or production guarantees have been validated.
Only three deterministic seeds per phase support descriptive sensitivity, not
statistical generalization. Exact search is intentionally bounded to small cases.

New CI runs QueryGuard tests and a fresh full benchmark/independent verification on
Python 3.10/3.12/3.13. Existing workflows remain untouched. Run root tests and frozen
V4/V5 validation separately as documented by the repository; skipped jobs are not
passing jobs. This PR is for review into research/queryguard, with no automatic merge.
