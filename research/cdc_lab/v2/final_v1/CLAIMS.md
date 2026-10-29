# Independent manuscript claim audit

Scope: every quantitative statement and technical paragraph in `manuscript.tex`,
against the immutable main snapshot `583b90bb5a8bc33b99e4812c4a29399d416beb19`.
No new experiment outcome or novelty is asserted. `audit.py` fails on disagreement;
`CLAIM_AUDIT.json` records its actual outcome and evidence hashes. The candidate is a
revision of V2; all earlier source, PDF and result files remain unchanged.

| Claim / location | Evidence and independent check | Assessment / boundary |
|---|---|---|
| Abstract: stable state can be wrong; IDs do not order distinct changes | `cdc_interactive.scenario('stale_update')`, `Materializer.apply`; hand-calculated k0 v4 then v3 and independent maximum-version target in `audit.py` | Arrival and ID-only end at deleted v3; version guards retain live v4. General source-version validity is assumed. |
| Abstract / evidence: original 126 principal + 36 bounded rows reproduce | Original `cdc_lab/results/run-1`, V2 `baseline-reproduction-1`, `verify.compare`, fresh `/tmp` rerun | Every non-timing row field and original configuration/hash match. Same implementation, not separately authored replication. |
| Architecture: schema and source ordering | `canonical`, `cdc_demo.validate`, `Materializer.apply` | Stable immutable event IDs, string payload, bool deletion and authoritative per-key integer versions; arbitrary source ordering inference not implemented. |
| Architecture: oracle independent of processor transitions/validator | `cdc_interactive.oracle`; separately expressed `independent_target` in audit | Canonical maxima independently reduced for all 144 rows. Both assume the same specification. Oracle is not an external authority or proof. |
| Architecture: three policies | `STRATEGIES`, `Materializer.apply` | Arrival overwrites, ID-only checks remembered IDs, version adds lower/equal-version guards. Clarified: arrival stores no identity ledger; unlimited capacity applies to ID-based principal policies. |
| Architecture: tombstones | `Materializer.state`, assignments in `apply` | One current record per key. A latest deletion remains a tombstone until superseded; this is not indefinite retention of all historical tombstones. Candidate wording narrowed. |
| Architecture: whole-input conflict rejection | `replay(validation='global')`, `cdc_demo.validate`, retained rejected rows | Both ambiguity classes reject before any policy processes input. Not an online-detection success. |
| Architecture: checkpoint serialization / restore | `Materializer.snapshot/restore`, `replay` loops | JSON logical state and ID ledger, not disk/fsync/transactional CDC recovery. Lost attempts = interruption minus checkpoint. |
| Architecture: monotonicity counters | `deliver` and `violations` | Attempted, committed-prefix, recovered writes separate; restore not counted as stale write. “Discarded on restore” claim scoped to completed recoveries. |
| UI: standard library, self-contained HTML/JS, loopback and request-local state | `Handler`, `serve`, embedded `HTML`; HTTP and installed-wheel browser tests | No cloud, arbitrary-data upload or external frontend dependency. Local test tool Playwright is an additional testing dependency. |
| UI: nine scenarios and three strategies | `SCENARIOS`, `STRATEGIES`, `/api/scenarios` | Eight principal scenarios plus separate ledger-expiry scenario; three policies. |
| UI: four orderings and settings | `evaluate`, HTML controls | Native/reverse/shuffle/version ordering; keys 1..64, seed, checkpoint/interruption, capacity, validation. Input treatments differ. |
| UI: actual/oracle and reasons | `wrong_keys`, `evaluate`, HTML render | Missing/unexpected key, stale/newer version, payload/tombstone mismatch. Rejected/incomplete runs have null completed correctness. |
| UI: trace decisions and stepping | `deliver`, trace checkpoint/restore records, slider/next controls, browser smoke | Snapshot rows have no event decision; event rows carry decisions, before/after and ledger size. |
| Walkthrough: deterministic stale-delete under one minute | Installed-wheel Chromium smoke assertion `<60s`; fresh local result in verification record | Local observed 2.342s; not a user study or general latency guarantee. No seed search. |
| Walkthrough: ID-only wrong / version correct | Hand calculation plus audit replay and DOM assertions | Confirmed for prescribed native preset only. |
| Walkthrough: three keys, c=4/i=8, four lost/replayed attempts | `audit.py` and real browser recovery interaction | Counts both 4, version final correct and redelivery stable. Restore operation distinct from applied write. |
| Walkthrough: finite capacity 4 misses conflict / unlimited stops | Online expiry evaluation, DOM assertions | Latest version correct may coexist with historical conflict miss; stopped run has no completed verdict. |
| Walkthrough: whole-input validation rejects | `validate`, HTTP tests | Global preflight tested through Python/HTTP. Existing browser script does NOT switch back to global validation after the unlimited stop; candidate no longer claims that every interaction is browser-asserted. |
| Evidence: preregistration | Original protocol and V2 protocol, recorded protocol/source hashes | Repository preregistration, not external registration. Earlier commit IDs recorded in V2 README; no priority/novelty inference. |
| Evidence: 144 principal rows | Exact Cartesian key set checked: 2 sizes (8,64) x 3 seeds (7,17,29) x 8 conditions x 3 policies | All retained rows replayed and compared, not only totals. |
| Evidence: correct/incorrect/rejected | JSON-authoritative rows and audit table assertions | Arrival 24/12/12; ID-only 30/6/12; version 36/0/12. Caption fixed: completed and rejected shown, not “rejected excluded”. |
| Evidence: six configs per isolated control | Per-scenario row checks and replay | All policies pass ordered, duplicate-only, ordered delete/reinsert and checkpoint recovery. Negative/neutral findings retained. |
| Evidence: stale deletes and reverse redelivery | Per-scenario results, all policy replay fields checked | Arrival/ID-only fail all six stale-delete configurations; reverse recovery redelivery adds six arrival failures only. |
| Evidence: 72 expiry rows | Three policies x 4 capacities x 3 seeds x 2 orders; every row freshly reexecuted | FIFO; duplicate hits do not refresh. Keys/state/tombstones not bounded. |
| Evidence: expiry probe-order | Per-row checks for version replay | Conflict-first detected only unlimited; exact-then-conflict detected at 4/16/unlimited, missed at 0. Same ordered bootstrap across seeds; repeated rows not independent. |
| Evidence: five timings per row | Median and five-sample checks; runner loops | Principal includes validation/copies/serialization/traces; expiry includes bootstrap/probes without traces/checkpoints. Original unqualified timing wording corrected. No speedup/throughput inference. |
| Related work: method context | Bibliography and `LITERATURE.md` | Established streaming, reference specifications, logical snapshots, visualization. No claim to invent methods or to benchmark the cited systems. NoREC removed because no substantive technical comparison was supported. |
| Limits: no cloud, concurrency, epochs, durable sink, GC, or exactly-once guarantee | Complete small implementation inspected | Accurate scope. State equality does not count external side effects. Finite identity capacity does not bound total state. |
| Reproducibility: source hashes/platform/config/timings retained | Original and V2 artifact metadata / manifest / CSV validation | All evidence references immutable paths; historical timing values retained, not refreshed in place. |

## Source/access distinctions

The earlier `VENUE_REQUIREMENTS.md` claims an October 13 official CFP verification;
the earlier build report and README predate that update. Neither is silently treated
as a current verified rule. See `VENUE_EVIDENCE.json` and `READINESS.md` for today's
attempts, inherited rules, author/CFP/Paper 1 blockers and actual production build.

Paper 1's submitted manuscript is absent from the main tree. V4/V5 code/results are
available and show thematic overlap (silent corruption, independent oracle,
replay/commit recovery). A defensible textual and duplicate-submission assessment
requires the actual submitted paper and status; different titles are insufficient.
Other research (including QueryGuard) is on separate branches, not in this main snapshot, and is not
modified. All pre-existing tracked files on main are protected by SHA-256.
