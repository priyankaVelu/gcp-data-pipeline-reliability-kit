# Experiment Suite v2 protocol

## Purpose
Test robustness across fault prevalence and compare the reliability controls against explicit alternative implementations rather than a no-control baseline.

## Frozen confirmatory matrix
This protocol is declared before examining v2 results.

- Dataset sizes: 1,000; 10,000; 100,000 rows.
- Deterministic seeds: 1103, 2207, 3301, 4409, 5501.
- Fault rates: 0.1%, 1%, 5%, 10%.
- Seven timing repetitions per configuration; the per-configuration median is retained.
- Four scenarios: duplicate replay, null business keys, partial-processing recovery, bounded recovery.

With 3 sizes x 5 seeds x 4 rates x 4 scenarios x 2 strategies, the default run produces 480 observations.

## Comparators
- Duplicate replay: sort/group deduplication vs set-based first-occurrence control.
- Null business key: explicit validation loop vs kit validation control.
- Partial recovery: append/replay comparator vs idempotent replay control.
- Bounded recovery: direct timestamp predicate vs kit bounded-backfill control.

Comparator code is intentionally simple and disclosed in the repository. It is not claimed to represent a particular commercial product or industry standard.

## Outcomes
- Injected faults and detected faults.
- Correct-run indicator based on a predeclared invariant.
- Detection rate aggregated across seeds.
- Correct-run rate.
- Local Python runtime, using seven repetitions and medians to reduce timer noise.

## Predeclared invariants
- Duplicate replay: exactly n unique events remain and all injected duplicates are reported.
- Null-key validation: all injected invalid business keys are reported.
- Partial recovery: final output contains exactly n unique events; duplicate replay is identified.
- Bounded recovery: output exactly matches the half-open interval [start,end).

## Interpretation boundary
These are synthetic in-process Python experiments. They test algorithmic behavior and local overhead only. They do not establish BigQuery, Dataflow, Airflow/Composer, network, storage, or distributed-system performance.

Fault-rate sensitivity applies directly only to scenarios where the rate changes injected faults. For recovery-window scenarios the rate is retained as a matrix label for balanced execution, not as a causal factor; analyses must not imply otherwise.

## Evidence rules
Preserve all raw outputs. Do not edit generated results. Keep commit SHA, Python version, configuration, and SHA-256 digest. Unexpected or negative results remain part of the evidence. Any post-result protocol change is exploratory and must be labeled as such.
