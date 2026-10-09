# DSN 2027 validity amendment — proposed v4 correction (2026-10-09)

This amendment is **post-result** and does not change or replace the frozen v4 protocol, original raw CSV, original summary, or original failure log. It is an exploratory correction branch. No corrected results are claimed until tests and the full suite have been rerun and independently reviewed.

## Issues found
1. Recovery replay records were prepended to the input, so a replay copy could appear before the original record. This does not represent a replay **after** a processing interruption. The implementation now appends replay records after the original input. This is only a chronology correction, **not** a complete checkpoint-state recovery simulation.
2. The old fault-detection numerator counted all tagged late/conflicting events as detected whenever event-time resolution was enabled, even though no explicit detection alert was emitted. The implementation now credits **zero** late/conflict detections until an actual detection mechanism with independently auditable evidence is implemented.

## Further issues requiring resolution before paper submission
- The canonical oracle includes records whose business keys are corrupted by injection. Consequently, key rejection can lower oracle state correctness and be mislabeled as false rejection. Specify whether the target is perfect source-state reconstruction or safe observable-state handling; distinguish unrecoverable source corruption from incorrect processing.
- The existing recovery strategy is not a true checkpoint/restore implementation: the processor receives a combined input stream, not persisted partial state plus post-crash continuation. Either implement checkpointed state or relabel the experiment as **replay deduplication**, not recovery completeness.
- The current `fault_detection_recall` metric mixes removal of invalid/duplicate records with event-time resolution and replay behavior. Define per-fault independently observable detection signals, with explicit true-positive/false-positive accounting, before making aggregate detection claims.
- `duplicate_leakage_count` counts only canonical event IDs, omitting some injected conflicting events. Audit numerator and denominator semantics.
- Run focused regression tests, reproduce all configurations, audit generated raw/summary consistency, and compare corrected outputs with the preserved v4 run. Do not overwrite historical results.
- Perform a literature review and verify tool-paper eligibility, novelty, and reproducibility; these changes alone do not establish publishable contribution.

## Status
Code chronology and inflated temporal detection credit corrected on this branch. Full validation and new results **pending**. Keep this amendment linked in any future manuscript and disclose post-result changes transparently.
