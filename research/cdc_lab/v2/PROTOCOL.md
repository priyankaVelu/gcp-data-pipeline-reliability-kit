# CDC Lab V2: isolated controls and visible recovery — protocol 2.0

Commit before implementation or measurement. Repository preregistration only.
No original protocol, run-1 artifact, configuration or manuscript is replaced.
Target is a diagnostic/educational demonstration, not a new CDC algorithm.

## Reproduction

Run the original runner unchanged in a new V2 baseline-reproduction directory.
Verify 126 principal/36 bounded rows and SHA256 manifests, CSV/JSON parity and
exact non-timing row equality to run-1. Compare timing descriptively, not for speedup.
Record both source commits and code/protocol hashes. Do not claim an independent
implementation replication: this is independent execution plus artifact validation.

## New principal matrix

Keys [8,64], seeds [7,17,29], strategies arrival/id_only/version, five repetitions.
Eight scenarios = 144 observations:
- ordered: live versions 1,2, monotonically delivered per key.
- duplicate_only: same live stream; seeded selection repeats an event immediately
  after itself. No per-key inversion, tombstone or recovery. No additive side effects.
- ordered_delete_reinsert: versions 1,2,3(delete),4(live), per-key order maintained.
- stale_update: canonical versions 3(delete),4(live); deliver all v4 before all v3.
  Distinct identities make this a guaranteed stale-delete counterexample.
- conflicting_id: ordered live stream plus altered payload with same event ID.
- same_version_conflict: ordered live stream plus altered payload with NEW ID and
  same key/version. Shared global validation must reject both before processing.
- checkpoint_recovery: ordered delete/reinsert; serialized checkpoint floor(L/3),
  interruption floor(2L/3), restore earlier state+ledger and replay suffix.
- post_recovery_redelivery: same as checkpoint_recovery, then full reverse redelivery.

Oracle is a separate batch maximum-version reduction over canonical input before
injection, with independently implemented identity/key-version conflict checks.
Processor validation uses existing schema checks; oracle does not call processor
transitions or shared conflict validation. No authoritative-version inference.

Report state_correct (null for rejected/incomplete input), wrong keys/reasons,
attempt/restart/redelivery applied/duplicate/stale/conflict counters, lost attempts,
replayed attempts, checkpoint/interruption offsets. Monotonicity has separate
attempted-write, committed-prefix, and recovered-write violation counts. Restore
rollback is a model operation, not a stale write or durable-state correctness fault.
Redelivery state stability and oracle equality remain separate. Median runtime
includes validation, copies, serialized checkpoint, replay and traces; excludes
canonical generation, oracle computation, artifact scoring and disk I/O. Preserve all
five perf_counter_ns samples; rotate strategy order. Not comparable in absolute speed
to the original runner because the V2 trace changes measured work.

## Separate online expiry matrix

16 keys, ordered versions 1..4; capacities [0,4,16,unlimited], strategies three,
seeds three, probe orders [conflict_first,exact_then_conflict] = 72 observations.
FIFO insertion eviction; duplicate hits do not refresh. Identity b0:v1 is outside
finite capacity. Conflict probe changes its value. Both probe orders start from fresh
identical completed state. Whole-input validation disabled for probes so finite
memory is observable. Record recognized duplicate, ledger peak, detected conflict,
pre/post state equality, and all timings. No general detection rate or exactly-once
claim; state/tombstones unbounded. The seed is recorded but ordered bootstrap is
identical across seeds; these are repeated configurations, not independent samples.

## Interactive interface and verification

A standard-library loopback HTTP UI selects scenario, strategy, ordering, checkpoint,
interruption, capacity, validation mode, and seed. Each run is stateless; event traces
show attempts, checkpoint/restore boundaries and restarted/redelivered operations.
Wrong-key reasons compare actual state to the canonical oracle. A complete conflicting
input rejected globally is not counted as successful online conflict detection.

Tests must cover hand-calculated oracle outcomes, same-version and same-ID ambiguity,
ordered/duplicate controls, checkpoint rollback/counter separation, snapshot isolation,
expiry probe-order effects, configuration errors, HTTP endpoints and live UI controls.
A five-minute scripted walkthrough must reproduce baseline failure within a minute.

Use fresh directories only. Save CSV, JSON, SHA256, config, Python/platform, Git HEAD,
tracked dirty status, dataset/protocol/source hashes, repetitions and failure.json on
unexpected error. Preserve all negative outcomes, no exclusions by result. Forbid
non-finite timings and duplicate configuration rows. Verify all historical hashes.
Paper 1 is protected; its absent submission source needs owner review for overlap.
