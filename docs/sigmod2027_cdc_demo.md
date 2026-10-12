# SIGMOD 2027 CDC Replay Correctness Demonstration — draft

## Scope and observed implementation
This branch adds a standalone, standard-library, synthetic CDC correctness lab alongside the existing reliability CLI. Existing CSV duplicate/null/freshness/current checks are not replaced. V4/V5 research branches and historical results are not modified.

| Capability | Evidence / status |
|---|---|
| Existing reliability CLI | Main repository README, docs/cli.md, tests/test_cli.py |
| Deterministic duplicates and out-of-order arrivals | `scenario(seed)`, added |
| Earlier committed checkpoint and lost uncommitted suffix | `replay(..., checkpoint_after, interrupt_after)`, added |
| Logical state plus event-ID ledger restored across simulated restart | JSON serialization/deserialization, added |
| Independent oracle | `oracle()`: batch max-version reduction, conflict validation, added |
| Conflicting event IDs and same-key/version | Whole-stream validation, added |
| Idempotent redelivery after recovery | Replay entire input after recovery and assert unchanged snapshot, added |
| Intentionally incorrect arrival-order baseline | `naive()`, added |
| JSON comparisons, recovery and invariants | `demonstrate()`, added |
| True durable storage, transactional offset commit, external CDC | Not implemented |
| Novelty, exactly-once, performance evidence | Not claimed |

### Semantics
Events have `event_id`, `key`, positive integer `version`, string `value`, and boolean `deleted`. Higher version wins; tombstones are retained, so a higher-version reinsert can restore a key. Conflicting payloads for the same event ID or for the same key/version are invalid. Input is validated against the complete event stream before execution; this is a bounded synthetic laboratory, **not** an online conflict detector.

The checkpoint is captured after `checkpoint_after` input events. Processing continues to `interrupt_after` without committing another checkpoint. The process is simulated as lost, the earlier checkpoint's logical state and deduplication ledger are serialized/deserialized, and events from the checkpoint offset to the end are replayed. All events are then redelivered to test idempotency. **Persistence is simulated only**: no disk write, fsync, transactional coupling, crash testing, or storage durability.

The oracle is a separate order-free batch reduction over the complete event set, preceded by an independent global conflict validation. It is not a formal proof or an external authoritative database.

## Five-minute interactive walkthrough
1. **0:00–0:45** Explain event IDs, versions, tombstones and the naive last-arrival-wins baseline.
2. **0:45–1:30** Run `python -m pipeline_reliability.cdc_demo --seed 7 --checkpoint-after 2 --interrupt-after 5`. Inspect `recovery.uncommitted_events_lost` and `recovery.replayed_after_restart`.
3. **1:30–2:15** Compare `baseline_state` to `oracle.state` using `baseline_wrong_keys`. A seed may not expose a baseline error; change the seed when needed. The adversarial unit test guarantees a reproducible counterexample.
4. **2:15–3:15** Inspect `corrected_state`, `oracle.verdict`, `recovery_counts` and all `invariants`. Explain how state **and** dedup ledger survive logical restart.
5. **3:15–4:15** Run `--seed 19 --checkpoint-after 0 --interrupt-after 12`, then `--checkpoint-after 12 --interrupt-after 12` to compare restart boundaries.
6. **4:15–5:00** Run `python -m unittest discover -s tests -v`; discuss conflicting payload permutations, delete/reinsert, invalid input and the durability limitation.

Exit codes: 0 invariant pass, 1 invariant failure, 2 invalid configuration. Output is a single JSON object.

## Proposed four-page SIGMOD demonstration paper outline
**Page 1 — Motivation and problem statement.** Define CDC duplicate delivery, out-of-order arrivals, stale overwrites, replay after interruption, and why naive last-arrival-wins fails. State assumptions about stable event IDs and monotonically increasing per-key versions.

**Page 2 — Architecture and implementation.** Diagram synthetic generator, intentionally incorrect baseline, corrected replay state machine, checkpoint state plus dedup ledger, simulated restart and independent batch oracle. Define invariants and JSON schema.

**Page 3 — Demonstration experience and observed findings.** Five-minute interactive seed/checkpoint controls; show measured outcomes *only after CI/local tests run*. Include a deterministic adversarial baseline counterexample and permutation conflict tests. Separate observed results from proposed claims.

**Page 4 — Related work, limitations, reproducibility and future work.** Compare only after literature verification with CDC systems, event sourcing, fault-tolerant streaming, exactly-once processing, model-based testing and differential testing. Explicitly note lack of durable storage, crash consistency, external integration, scale benchmarks and formal proof. Describe a future durable-checkpoint implementation as proposed work, not an achieved result.

**Proposed contribution (not established novelty):** a reproducible, audience-driven teaching and diagnostic demonstration exposing CDC correctness counterexamples and replay invariants. No submission has been made.

## Test commands
```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python research/test_paper_experiments_v4.py
python research/test_paper_experiments_v5.py
python -m pipeline_reliability.cdc_demo --seed 7 --checkpoint-after 2 --interrupt-after 5
```
The GitHub Actions workflow runs the full unittest suite and research tests if those files exist on this branch. Missing research test files are explicitly logged, not represented as passing regressions.
