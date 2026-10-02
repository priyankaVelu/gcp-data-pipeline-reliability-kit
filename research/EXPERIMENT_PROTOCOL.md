# Experiment protocol

## Objective
Evaluate whether explicit reliability controls improve correctness and recoverability under controlled data-pipeline faults.

## Baseline
A minimal pipeline without the reliability control under test.

## Treatment
The same workload with one or more reliability controls enabled.

## Data
Use generated synthetic event data with deterministic seeds. Public datasets may be added later with their licenses and provenance recorded.

## Fault scenarios
- duplicate input events
- missing/null business keys
- conflicting current-state records
- delayed events
- partial-batch failure
- replay of an already processed interval

## Required repetitions
Each benchmark configuration should be repeated with multiple deterministic seeds. Report all observations and aggregate statistics; do not discard unfavorable runs without a documented protocol reason.

## Primary outcomes
1. Output correctness.
2. Fault detection.
3. Idempotent recovery.
4. Runtime overhead.

## Evidence integrity
- Preserve raw machine-generated results.
- Record code commit SHA with each run.
- Record environment/dependency versions.
- Do not fabricate or manually alter results.
- Document failed experiments as failures.
- Separate exploratory analysis from confirmatory results.
