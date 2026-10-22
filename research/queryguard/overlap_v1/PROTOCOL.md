# QueryGuard overlap-aware planner — experiment protocol 1.0

Synthetic exploratory study. No novelty, production or calibrated cost/risk claim.
Commit this protocol before implementations are measured. Preserve the original
additive PoC and all Papers 1/2 files; results use a new output directory per run.

## Model and assumptions

Faults are mutually exclusive scenarios with rational probabilities summing to at
most 1; the remainder is no fault. A scenario can name a compound fault outcome.
No independence assumption is used. Every exposed (fault,consumer) pair is unique
and has a severity fraction in [0,1]. Consumer loss is a nonnegative impact per
incident. Expected pair loss is probability * consumer loss * severity. Consumer
losses are assumed additive across distinct consumers; do not represent the same
business loss twice under two consumer names. Expected losses are not observed
frequencies or independently calibrated estimates.

Each check declares a deterministic set of detectable (fault,consumer) pairs.
Selecting checks covers the union of these sets: duplicated incidence/overlapping
checks cannot increase utility for an already covered pair. Residual modeled risk
is the sum of weights of uncovered exposed pairs. A covered pair represents assumed
verification-enabled containment of that consumer loss, not evidence that executing
a real query fixes a downstream failure. Detection and remediation assumptions are
strong and explicit; no false-positive/negative or intervention-latency model.

Costs: sum of one setup cost for every scan group used by any selected check, plus
each selected check's incremental evaluation cost. Checks can use several groups;
shared cost requires explicitly identical, compatible scan-group identities, not
merely a common dataset name. All costs synthetic nonnegative rational units.
No query execution, cloud billing, join planning or scan-sharing calibration.

## Policies and tie rules

Exact: enumerate feasible subsets, maximizing union risk reduction, then minimize
cost, then check count, then lexicographically sorted IDs. At most 20 checks; reject
larger instances explicitly. Exponential time, no large-instance scalability claim.

Risk-aware greedy: highest newly protected expected loss / marginal shared cost.
Coverage greedy: highest number of newly covered exposed pairs, ignoring weights.
Cost-aware greedy: highest newly covered pair count / marginal shared cost (an
unweighted coverage-per-cost baseline). All recompute after each selection and only
add budget-feasible positive-gain checks. Free positive gains rank before paid ones;
ties prefer greater absolute gain, lower marginal cost, then ID. These are defined
heuristics, not claims of canonical baselines or approximation guarantees. Setup
costs can cause every singleton greedy to miss a jointly beneficial shared-scan
bundle; preserve that negative fixture. Zero total risk ratios are undefined/null.

## Frozen fixtures and experiment matrix

Fixtures: overlap (hand-derived union risk 52, not additive 72), shared-scan trap
(original PoC objectives represented by explicit incidence, budget 7, exact risk 16,
all singleton greedies risk 12), zero-cost and empty/zero-risk edge cases in tests.

Seeded instances: checks [6,10,12], seeds [7,17,29], incidence probabilities [0.2,0.6],
budget fractions [1/4,1/2,3/4] of full-plan shared cost (floor to synthetic units),
4 policies. 54 configurations x 4 = 216 rows. Each uses 8 fault scenarios, 5 consumers,
4 scan groups; probabilities are seeded positive integer weights normalized to a
combined 4/5 fault probability. Consumer impacts are integers 1..50; severity 1.
Exposures are seeded pair draws at probability 0.6, with each scenario guaranteed an
exposed consumer. Setup costs 1..9, evaluation costs 0..3; each check uses one group,
with every fifth check using a second group. Incidence draws use the frozen density;
empty check incidence is permitted. Inputs depend only on seed/check-count/density,
not policy or budget. No outcome-based seed selection or exclusions.

Three fresh timed runs per policy; rotate policy order by configuration index.
Timing includes policy preparation and optimization, excludes generation, independent
validation/scoring and disk I/O. Retain all perf_counter_ns samples and local median.
Correctness oracle: separately authored subset enumeration and direct consumer-wise
loss calculation, without calling optimized cost/utility functions. Use hand cases,
small random problems and independent verification of every reported selected plan.
Report objective, residual risk, coverage, cost, exact gap/ratio, plan IDs, feasibility,
search work and timing. No significance test, universal superiority or warehouse
throughput/cost estimate. Ties at optimum count as matches without claiming uniqueness.

## Integrity

JSON inputs and outputs plus CSV, SHA-256 manifest, source hashes, protocol hash,
full Git commit, dirty status, Python/platform, seeds, configuration, repeats and
workload hashes. Store exact rationals as strings; runtime samples are finite floats.
Reject existing output paths. On unexpected failure preserve failure.json and abort;
never turn a technical error into an objective-zero row. Validate row counts, unique
configuration/policy keys, feasibility, objective accounting and exact bounds. Run
legacy PoC, full unit tests and frozen V4/V5 regression tests. Preserve all historical
research bytes with the baseline manifest and keep PR target research/queryguard.
