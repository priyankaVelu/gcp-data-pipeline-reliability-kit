# Experiment protocol

## Objective
Evaluate whether explicit reliability controls improve correctness and fault detection under controlled synthetic data-pipeline faults, and quantify their local execution overhead.

## Study design
For each scenario, execute a deliberately minimal baseline and a controlled treatment on the same generated workload. The baseline omits only the reliability control under test. Do not describe the baseline as representative of all production systems.

## Data and reproducibility
Use generated synthetic event data only. Generation uses deterministic seeds. Every result records the Git commit SHA and Python version. Raw CSV output is hashed with SHA-256 and the digest is stored in the summary.

## Confirmatory v1 matrix
- Dataset sizes: 1,000; 10,000; 100,000 rows.
- Seeds: 101, 202, 303, 404, 505.
- Fault injection rate: 1%.
- Scenarios: duplicate replay, null business key, bounded backfill, stale data.
- Variants: baseline and controlled.

Changes to this matrix after examining results must be documented as exploratory or as a new protocol version.

## Outcomes
1. Fault detection rate = detected injected faults / injected faults.
2. Correct-run rate = runs satisfying the predeclared scenario invariant / total runs.
3. Local runtime: mean and median elapsed milliseconds.

## Scenario invariants
- Duplicate replay: controlled output has exactly the original number of unique event IDs and reports all injected duplicates.
- Null business key: controlled validation reports every injected null key.
- Bounded backfill: controlled output contains exactly events in [start, end).
- Stale data: controlled freshness check flags an event two hours old when the threshold is one hour.

## Limitations
The experiment is an in-process Python synthetic benchmark. It does not measure network, storage, scheduler, BigQuery, Dataflow, or Cloud Composer behavior. Timing results therefore support only local implementation-overhead observations. Larger cloud experiments require a separately specified protocol and cost/environment record.

## Evidence integrity
- Preserve raw machine-generated results.
- Record code commit SHA and environment.
- Do not fabricate, manually alter, cherry-pick, or suppress observations.
- Document failed experiments as failures.
- Keep exploratory analyses separate from confirmatory results.
- Make publication claims only after inspecting generated evidence and applicable literature.
