# Overlap-aware consumer-risk verification planner — v1

Status: a synthetic, static planning model and reproducible experiment, not a
production verifier or a validated novel algorithm. No query or warehouse execution.
Python 3.10+; standard library only. Run commands from the repository root.

## Reproduce a plan

```sh
python -m research.queryguard.overlap_v1 --fixture overlap --budget 6
python -m research.queryguard.overlap_v1 --fixture shared_scan_trap --budget 7 --policy exact
python -m research.queryguard.overlap_v1 --fixture shared_scan_trap --budget 7 --policy risk_aware_greedy
python -m research.queryguard.overlap_v1 --input research/queryguard/overlap_v1/examples/overlap.json --budget 6 --policy cost_aware_greedy
```

`--policy` supports `exact`, `risk_aware_greedy`, `coverage_greedy`, and
`cost_aware_greedy`. Output contains selected checks, union coverage, modeled risk
reduction/residual risk, cost, feasibility and search/candidate work. Exit 0 means a
plan was computed, not that a real pipeline is correct; exit 2 denotes invalid input.
Exact search rejects more than 20 checks. `examined` counts feasible subsets for exact
search and candidate evaluations for greedy; these counts are not equivalent work.

## Model: no duplicate utility or scan billing

A `Fault` is a mutually exclusive scenario, not an arbitrary independent marginal
fault. Probabilities sum to at most 1, with the remainder representing no fault.
Summing to at most 1 does **not** prove exclusivity: it is an input contract. To model
co-occurring faults, supply disjoint joint-outcome scenarios, including compound
outcomes, with their joint probabilities. No independence assumption is made.

Consumers have nonnegative per-incident impact. Unique `Exposure(fault, consumer,
severity)` records give a fraction of that consumer's impact at stake. Each exposed
pair has weight `probability * consumer impact * severity`. Distinct consumer losses
are assumed additive: aliases for the same business loss must not be supplied as
separate consumers. This is expected additive loss under a specified scenario model,
not a learned probability of general pipeline failure.

Each check declares a **set of detectable exposed pairs**. Detection can be
consumer-scoped; a global detector should explicitly list every exposed consumer
it is assumed to protect. For selected checks S:

- `covered(S)` is the union of their pair sets;
- `risk_reduction(S)` sums each covered pair's weight once;
- `residual_risk(S)` sums uncovered pair weights;
- `coverage(S)` counts distinct covered pairs, not checks, faults or SQL rows.

The same pair listed twice or covered by several checks contributes once. The same
consumer affected in two mutually exclusive scenarios contributes the probability-
weighted incident loss in each alternative, not two simultaneous incidents. Exposures
with duplicate pair identities are rejected rather than summed.

A check's scan groups identify compatible shared execution work. Cost is the sum of
one setup charge per distinct used group plus each selected check's evaluation cost.
Checks may require several groups. Repeated group names do not multiply charges.
Shared scan identities require assumed compatibility; a common dataset name alone
does not establish reusable I/O, projection, predicate or engine compatibility.
Setup/evaluation costs are nonnegative synthetic units, not bytes scanned or dollars.

All probabilities, severities, costs and risks use `fractions.Fraction` internally.
JSON represents exact rationals as strings (`"1/5"`, `"52"`); prefer these over
floating-point input. Runtime samples/summary ratios are floating-point observations.
Unknown IDs, unmodeled incidence, duplicate record IDs, invalid probabilities,
negative/non-finite numbers and nonconforming JSON schemas are rejected.

## Policy definitions and limits

| Policy | Feasible next-check criterion |
| --- | --- |
| Exact | All feasible subsets; maximize modeled risk reduction |
| Risk-aware greedy | Marginal union risk / marginal shared cost |
| Coverage greedy | Marginal count of newly covered exposed pairs |
| Cost-aware greedy | Marginal pair count / marginal shared cost; unweighted baseline |

Every greedy step recomputes gain and incremental scan charges. Positive free gains
rank before paid gains for the two ratio policies. Coverage greedy remains an
absolute coverage-gain baseline. Ties prefer larger absolute gain, then smaller
incremental cost, then lexicographic ID. Exact ties minimize cost, then selected-check
count, then lexicographically sorted IDs. Input order does not affect results.

Shared setup costs can make singleton greedies miss useful bundles. The hand fixture
has scan setup 5 plus evaluation 1: A and B cost 6 each or 7 together, while C costs 6
on another scan. Exact picks A+B (risk reduction 16); all three greedies pick C (12).
This is a deterministic limitation, not an argument for universal exact-planner
superiority at useful scales. Exact search is exponential; 20 is an explicit safety
limit, not a scalability claim. No approximation guarantees are asserted.

The overlap fixture gives A risk reduction 22 and B 50. Together they give **52, not
72**, because their common `(f1, critical)` exposure is credited once. Adding a
redundant detector changes no risk utility. Direct costs and expected losses are
checked against a separately authored consumer-wise oracle.

## Reproduce and inspect the retained experiment

```sh
python -m unittest discover -s research/queryguard/tests -v
python -m unittest discover -s tests -v
python research/test_paper_experiments_v4.py
python research/test_paper_experiments_v5.py
python -m research.queryguard.overlap_v1.experiment --output /tmp/queryguard-new-run
python -m research.queryguard.overlap_v1.verify /tmp/queryguard-new-run
```

Output paths must not exist. The CLI runs the matrix in `PROTOCOL.md`: 18 seeded
instances, 54 instance/budget configurations, four policies, **216 observations**, and
three fresh timing samples each. Full JSON inputs, results JSON/CSV, hashes, seeds,
full Git commit/dirty status, source/protocol hashes and Python/platform are retained.
`results/run-1/` was generated from commit
`d16ae021e0ea2c22650ed5c39444659accedcc14` with no tracked changes. The protocol was
committed before measured execution; its free-gain wording was clarified before the
first run to distinguish ratio policies from absolute coverage greedy.

Every selected plan was independently costed/scored. All 54 exact optima, including
tie-breaking, were independently enumerated by the direct reference implementation;
the artifact verifier repeats that check. It also regenerates inputs from declared
seeds, checks budgets, row uniqueness/matrix membership, medians, risk conservation,
CSV/JSON field parity and SHA-256 manifests. SHA-256 is integrity checking, not an
external signature or independent calibration of the supplied incidence matrix.

`results.json` is authoritative for types; CSV stores arrays as JSON cells, rationals
as strings, booleans as `True`/`False` and null ratios as empty fields. Two of the 54
configurations have zero optimal reduction. Their ratios are explicitly null, not
reported as 100% coverage. The match counts below include those objective-zero ties;
ratio summaries exclude them.

## Actual retained results

| Policy | Objective matches exact / 54 | Suboptimal | Worst defined objective ratio |
| --- | ---: | ---: | ---: |
| Exact | 54 | 0 | 1.000000 |
| Risk-aware greedy | 42 | 12 | 0.787916 |
| Coverage greedy | 45 | 9 | 0.813008 |
| Cost-aware greedy | 39 | 15 | 0.601279 |

No favorable seeds or rows were discarded. Risk weighting does not make a greedy
algorithm universally better: coverage greedy matched more optima in this matrix.
These counts describe only the seeded synthetic instances, not a statistically
independent population sample or practical superiority. Heuristics optimize different
local criteria, and the exact comparator optimizes the specified modeled risk.

Local medians across row medians (Python 3.12.14): exact 0.3434415 ms, risk-aware
0.220622 ms, coverage 0.185038 ms, cost-aware 0.1911375 ms. All raw samples are
retained; they are optimizer runtimes, not query, warehouse or production latency.
Policy preparation/search is timed; independent oracle checks, generation, scoring
and artifact I/O are excluded. Costs remain invented *model inputs*, explicitly
synthetic and never represented as measured costs. No production benchmark is claimed.

## Validation and preservation

The extension has tests for overlap, multi-scan billing, fractional boundaries,
zero/free/empty cases, duplicate/unknown identities, exact/greedy tie rules, random
exhaustive comparisons, seed stability, independent oracle logic, API/CLI input
validation, data corruption, technical failure preservation and output repeatability.
Legacy PoC tests still run. A dedicated CI workflow runs the QueryGuard suite on
Python 3.10/3.12/3.13 and generates/validates the registered matrix on Python 3.12.

`PRESERVATION.json` hashes **117 pre-existing tracked files outside QueryGuard**,
including Papers 1/2 scripts, results and manuscript PDFs. They are unchanged. The
only new file outside QueryGuard is the dedicated CI workflow. The legacy additive
PoC code and tests are unchanged. No existing result is overwritten; each rerun gets
a fresh directory. Unexpected failures produce `failure.json` and abort instead of
silently recording objective zero. Nothing is automatically merged or submitted.

## Remaining limitations

- Probabilities, consumer impacts, incidence, severity and scan compatibility are
  synthetic inputs; no uncertainty or robustness analysis or empirical calibration.
- Detection is deterministic; the model assumes verification-enabled containment
  of covered risk. No noisy checks, false positives/negatives, remediation delays,
  dependencies between checks, or causal proof that detection prevents loss.
- No lineage discovery or automatic inference of downstream consumer exposure.
- Mutually exclusive scenarios and additive consumer losses restrict interpretation;
  arbitrary overlapping marginal fault probabilities cannot be substituted safely.
- Static selection only: no adaptive execution, query engine integration, real
  shared scans, multi-budget scheduling or measured billing.
- Exact search and the independent oracle are deliberately limited to small cases;
  greedy has no asserted optimality/approximation guarantee under setup sharing.
- This is weighted set-union planning with synthetic setup costs, not an asserted
  novel method. Papers 1 and 2 are not extended by this change.
