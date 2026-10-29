# Bundle-aware QueryGuard: protocol 1.0

Repository preregistration, before measured execution; not an external registration.
Read BUNDLE_MILESTONE.md and the frozen overlap_v1 model, planner, protocol, tests,
experiment and independent oracle. All pre-existing tracked files remain unchanged.
A new versioned output directory is mandatory. No novelty/approximation claim.

## Algorithm frozen before benchmarks

Reuse overlap_v1's rational union-risk model and compatible scan groups. At each
iteration enumerate not-yet-selected bundles of sizes 1..min(k,remaining), for k=2
or k=3. Credit each newly covered scenario/consumer atom once. Charge the union of
unopened scan groups once plus each bundle member's evaluation cost. Filter by
remaining absolute budget and positive gain. Rank free gains before paid, then
risk/incremental cost, larger absolute gain, lower incremental cost, fewer members,
then lexicographically sorted bundle IDs. Add the winning bundle, recompute and
repeat. k=1 is supported solely as a singleton equivalence diagnostic. Stop when
no feasible positive-gain bundle remains. Input order must not alter decisions.

Candidate evaluations count all enumerated bundles (including infeasible/zero-gain
ones); exact's feasible-subset count and singleton candidate counts are different
work units. For n checks and a exposed atoms/g scan groups, a conservative bound is
O(n * sum(C(n,j), j=1..k) * (k+a+g)), polynomial for fixed k but potentially costly.
There is no optimality, approximation, or monotonic-improvement-in-k guarantee.
No best-of-baselines fallback or after-the-fact repair is used.

## Equal-budget sharing ablation

Shared mode is the original Problem unchanged. In no-sharing mode, replace each
(check,scan-group) use with a private scan group of the same setup cost. Preserve
faults, consumers, exposure/severity, check IDs/incidence and evaluation costs.
Singleton costs are identical across modes, but a joint plan pays setup per check.
Both modes use the SAME numeric budget floor(fraction * original shared full-plan
cost). Never normalize each mode by its own full-plan cost. No-sharing changes the
feasible set; risk reduction differences across modes are not solely a heuristic
quality effect. Report mode-specific exact optima and ratios.

## Frozen and expanded matrices

Frozen: use the original inputs.json (18 instances; sizes 6/10/12, seeds 7/17/29,
densities 1/5 and 3/5), and budgets 1/4,1/2,3/4 of shared full cost. All four original
policies plus bundle_2 and bundle_3, under two cost modes: 648 rows. Compare all 216
original-policy/shared-mode rows with historical results, every non-timing field.
Do not edit or regenerate the historical files.

Expanded: original generator unchanged; sizes 8/14, seeds 43/101/211, densities
1/5 and 3/5, same three budgets, six policies and two modes: 432 rows. No seed or row
selection by outcome. Total 30 base instances, 180 mode/budget cases, 1080 rows.
Keep frozen and expanded results separate as well as showing descriptive totals.

Three fresh timed executions per policy. Rotate order by mode/configuration index;
no warmup. Solver timing includes preparation/selection/result construction, including
bundle audit steps; excludes generation, ablation materialization, oracle and I/O.
Report all samples, median, selected cost/union reduction/residual risk, mode-specific
exact ratio/gap, and candidate work. Record separate end-to-end wall duration through
core artifact serialization (excludes final duration/manifest writes). It includes
expensive independent oracle verification; do not label it optimizer runtime.

## Fixtures and oracle

Preserve/import original overlap and shared_scan_trap fixtures. New hand-built
triple trap: A/B/C cover disjoint loss-8 atoms, share setup 5 and cost evaluation 1
each; D covers loss 15 with its own setup 5 and evaluation 1. Budget 8. Pair ratios
16/7 < 15/6; triple ratio 24/8 > 15/6. Therefore k=2 is insufficient on this designed
example. This is a constructed example, not a sampled prevalence estimate. Evaluate
all fixtures under both modes and all policies; retain negative/neutral outcomes.

Use unchanged independent consumer-wise measure and exhaustive oracle for every
selected plan and every mode-specific optimum (n<=14). Independently check bundle
step costs/gains from the accumulated plan. Tests also compare against a separately
written direct bundle enumerator on small random cases. Do not treat the optimized
exact policy alone as independent validation.

## Reporting, seeds and uncertainty

For every phase/mode/policy: exact matches, regret/defined ratio distribution, cost,
runtime and candidate counts. Paired +/=/− outcomes versus EACH singleton baseline
and bundle_2. Per seed, report mean defined optimum-ratio differences; summarize
these seed means with range, sample SD, and mean. Three seeds per phase, coupled
budgets/incidence/check prefixes: descriptive sensitivity, NOT confidence intervals,
significance, population accuracy or independent samples. Zero-optimum ratios stay
null; count their zero-utility ties but exclude only undefined ratio statistics.
Publish negative comparisons and non-improvement; do not imply larger k dominates.

## Integrity and scope

Record full commit, tracked dirty status, source/protocol hashes (including reused
v1 modules), locked historical artifact hashes, seeds/configuration, Python/platform,
JSON inputs, JSON/CSV results, summary and SHA-256 manifest. Reject existing output
paths; preserve failure.json on technical errors and abort rather than invent rows.
Tests: overlap, shared/private scans, fraction/zero/empty cases, deterministic ties,
invalid k/budgets, k=1 equivalence, local oracle comparisons, fixture, artifacts,
corruption, all existing tests and V4/V5. Preserve Papers 1/2 and all v1 results.

Original assumptions remain: mutually exclusive fault scenarios; additive consumer
incident losses; supplied deterministic detection/containment incidence; synthetic
costs. No real scan sharing, calibration, uncertainty in inputs, query execution,
production durability, practical performance superiority or novelty is established.
Review this as a fixed-charge/weighted-coverage lookahead heuristic, not a novel
algorithm. PR targets research/queryguard. No automatic merge or submission.
