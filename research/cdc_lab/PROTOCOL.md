# CDC Replay Correctness Lab: protocol 1.0

Repository preregistration for a demonstration artifact; not an externally reviewed
registration. Commit before experiment execution. Supersedes the unexecuted additive
backfill proposal on research/paper2-safe-replay-backfill for this SIGMOD demo target;
that proposal and all Paper 1 / V4 / V5 material remain unchanged.

Question: under immutable identities and comparable per-key versions, which failures
of arrival-order and ID-only materialization are visible through an independent
final-state oracle? Separate question: how does finite ID retention change duplicate
recognition and conflict detection, even when version guards preserve final state?
No exactly-once, durable checkpoint or algorithmic novelty claim is made.

Principal matrix: keys [8,64], seeds [7,17,29], scenarios [ordered, out_of_order,
duplicates, delete_reinsert, conflicts, checkpoint, redelivery], strategies
[arrival, id_only, version]. 126 observations; five timed executions per observation.
Four versions per key, v3 a tombstone, v4 a reinsert. Seeded shuffle uses Python
Random. Out-of-order/delete_reinsert append stale v3 after v4; duplicates repeat
selected IDs. Conflicts inject a different value with an existing ID. Conflicting
input must be rejected before processing by all strategies; this shared validation
is not online detection or evidence that replay policies detect conflicts.

Oracle: independent batch group-by-key maximum version over canonical input before
fault injection, including tombstones. Conflicts handled by the existing validator,
not by sharing processor transitions. Correctness measures final materialized state,
not external side-effect multiplicity. Preserve distinctions between detected invalid
input, correctness failures, and technical errors.

All strategies restore the same serialized logical state+ledger at floor(L/3),
interrupt at floor(2L/3), replay suffix, then (redelivery only) replay full input.
Other scenarios use checkpoint=interruption=0, so there is no lost work. Processing
before interruption is counted as attempted, then rolled back. No disk durability.
Arrival always overwrites. ID-only skips remembered IDs, otherwise overwrites.
Version skips remembered IDs and rejects lower versions; equal-version conflicts
are errors; tombstones retained. Ledger is unlimited in the principal matrix.

Metrics fixed before runs: wrong_keys and state_correct (null for rejected input),
nondecreasing_version (false if any successful write decreases version),
redelivery_state_unchanged (null unless redelivery requested), applied/duplicate/stale
counts before and after recovery, checkpoint_offset, interruption_offset,
lost_attempts and replayed_lost_attempts, restart_deliveries, redelivery_deliveries.
Runtime is five perf_counter_ns samples in ms, including validation, snapshot
copy/serialization, restart, redelivery; excludes generator, oracle, scorer and I/O.
No warmup; strategy order rotates by configuration index. Report local medians only.

Bounded-ID matrix: 3 strategies x capacities [0,4,16,unlimited] x 3 seeds = 36 rows.
16 keys, four versions, FIFO insertion eviction (duplicate hits do not refresh).
State/tombstones are unbounded. First replay oldest ID exactly, then replay that ID
with a conflicting payload. Online processor only: no whole-stream prevalidation.
Record ledger_peak, exact-redelivery recognition, changed state, conflict detection,
and local runtime. These are intentionally different validation conditions from the
principal matrix; never combine their accuracy statistics. No retention-horizon or
bounded-state guarantee: state is not bounded just because the ledger is.

Output: fresh directory only, CSV and JSON with row parity; Python/platform, UTC run
time, full source commit, tracked dirty status, seeds, repeats, protocol/runner SHA256,
workload SHA256 per row and artifact hashes. Fail on unexpected technical exception;
write failure.json, do not fabricate timing. No outcome-based exclusions. A new run
uses a new directory. Test determinism, oracle independence, corruption, snapshot
isolation, counterexample and matrix counts before runs. Retain negative outcomes.
