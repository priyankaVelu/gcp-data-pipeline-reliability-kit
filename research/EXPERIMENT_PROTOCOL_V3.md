# Experiment Suite v3 protocol — compound failures and recovery realism

## Purpose
Evaluate reliability behavior under more realistic combinations of faults and recovery states. This protocol is committed before v3 result values are observed.

## Confirmatory matrix
- Dataset sizes: 1,000; 10,000; 100,000 rows.
- Seeds: 1301, 2609, 3911, 5209, 6521.
- Fault rates: 0.1%, 1%, 5%, 10%.
- Recovery checkpoints: 25%, 50%, 75%.
- Seven timing repetitions per timed configuration.

## Scenarios
1. **Mixed duplicate + null-key faults.** Inject both faults into one batch. A reliable run must deduplicate and identify every remaining invalid business key.
2. **Out-of-order / late arrival.** Move a deterministic subset of events behind newer events. Compare arrival-order handling with event-time ordering; correctness is exact event-time order.
3. **Conflicting entity updates.** Multiple updates for the same business entity are shuffled. Compare arrival-order last-write with event-time latest-write; correctness is the latest event-time state per entity.
4. **Checkpoint recovery.** Simulate failure after 25%, 50%, or 75% of a batch and replay the full batch. Compare append replay with idempotent recovery; correctness is exactly one copy of each event.

## Outcomes
- Predeclared correctness invariant.
- Faults injected / detected where meaningful.
- Recovery duplicate count where meaningful.
- Local runtime median across seven repetitions.
- Raw observations plus commit SHA, Python version, configuration and raw-file SHA-256.

## Interpretation boundary
Synthetic, single-process Python only. No result may be presented as measured BigQuery, Dataflow, Composer/Airflow, distributed storage, network, or managed-cloud performance.

## Evidence rules
Preserve every generated raw result. Do not manually edit output. Do not remove unfavorable observations. Changes made after inspecting v3 results are exploratory and require a new protocol/version.
