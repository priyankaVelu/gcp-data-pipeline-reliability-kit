# SIGMOD 2027: CDC Replay Correctness Demonstration (draft)

## Feature inventory (2026-10-12)
| Capability | Status | Evidence / gap |
|---|---|---|
| Local reliability CLI | Existing | main README, docs/cli.md, tests/test_cli.py |
| Duplicate keys, null keys, freshness, duplicate current | Existing/tested in repository | CLI tests; not a CDC replay engine |
| V4/V5 synthetic research | Existing, preserved | Separate research branches and test scripts; not modified |
| CDC duplicate/out-of-order replay | New | pipeline_reliability/cdc_demo.py |
| Interrupted processing simulation | New, limited | In-memory checkpoint restore; not process crash durability |
| Independent batch oracle | New | oracle() independently computes maximum version per key |
| JSON interactive demonstration | New | CLI arguments seed and interruption position |
| External databases / actual CDC streams | Missing | No Kafka, Debezium or BigQuery connector |
| Throughput/latency benchmarks | Missing | No performance claims |

## Five-minute walkthrough
1. (0:00–0:45) Explain keys, versions, event IDs and the fictional synthetic dataset.
2. (0:45–1:30) Run `python -m pipeline_reliability.cdc_demo --seed 7 --interrupt-after 5`.
3. (1:30–2:30) Inspect JSON counters, checkpoint, and final state.
4. (2:30–3:30) Change `--seed 19 --interrupt-after 12` and compare oracle to replay.
5. (3:30–4:30) Explain duplicate suppression, version ordering, deletion tombstones and repeated replay.
6. (4:30–5:00) Discuss limitations: in-memory simulation, no durable transaction boundaries, no performance evidence.

## Demonstration paper outline
1. **Problem and motivation:** CDC consumers may observe duplicates, reordering and interrupted processing.
2. **Architecture:** seeded synthetic generator → replay state machine / checkpoint → independent batch oracle → JSON evidence.
3. **Research contribution (proposed, not yet validated):** an inspectable educational demonstration of correctness invariants and counterexamples; no novelty claim without related-work evaluation.
4. **Related work to investigate:** stream processing exactly-once semantics, event sourcing, CDC replay systems, stateful recovery, differential testing and model-based testing. Verify citations before manuscript submission.
5. **Audience interaction:** vary seed and interruption position, inspect duplicates, stale events, final state and oracle comparison.
6. **Evaluation plan:** fixed seeds, adversarial conflicting-version inputs, restart-boundary matrix, regression tests; report only measured outcomes.
7. **Limitations:** simulated restart, assumed unique event IDs and monotonically ordered per-key versions, no real database, no measured scale, no formal proof.
8. **Reproducibility:** Python standard library, fixed seeds, commands and machine-readable output.

This is a proposal outline, not a submission.
