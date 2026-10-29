# QueryGuard milestone 3: bundle-aware planning

**Status:** experimental design; no performance results claimed.

## Research question

Under a budget with shared scan-group setup costs, can bounded bundle lookahead improve consumer-weighted union risk reduction relative to singleton greedy selection without requiring exhaustive subset search?

## Required baselines

- Existing exact solver for small instances, serving as an objective-value oracle.
- Existing risk-aware singleton greedy.
- Existing coverage greedy.
- Existing cost-aware greedy.
- A bundle-aware risk-per-marginal-cost greedy policy with explicit maximum bundle size (e.g. 2 and 3).
- An ablation disabling scan sharing, to isolate the source of any gains.

## Proposed algorithm

At each step enumerate feasible, not-yet-selected check bundles of size 1..k. Score the *union* of newly protected (scenario, consumer) exposures, counted once, divided by the incremental setup + evaluation cost. Include deterministic zero-cost handling and tie-breaking. Select the best positive-gain bundle and repeat. Document complexity; do not claim approximation guarantees.

## Experiments

1. Preserve the existing shared_scan_trap fixture and overlap fixture.
2. Add an adversarial counterexample where k=2 is insufficient, if one exists.
3. Evaluate the prior frozen matrix *without modifying it*; append new experiment artifacts in a separate versioned directory.
4. Vary check count, budget, incidence overlap, and scan-group sharing.
5. Compare risk reduction, exact-optimum ratio, total cost, selection runtime, and candidate evaluations. Keep solver timing distinct from end-to-end run time.
6. Report negative and neutral results, uncertainty over seeds, and where lookahead loses to alternatives.
7. Validate all selected plans using the independent oracle; retain reproducible seeds and hashes.
8. Add tests and CI. Do not alter Paper 1, Paper 2, or historical QueryGuard results.

## Scientific cautions

These are synthetic risk and cost models. Detection does not automatically remediate an error. No BigQuery scan sharing, actual cloud cost, or publication novelty is established until independently validated. A positive comparison against weak greedy heuristics is insufficient to establish a new research contribution.

## Merge gate

Tests and CI green; complete reproducible comparisons; review whether any improvement is simply a known fixed-charge/coverage optimization heuristic; merge only into research/queryguard.
