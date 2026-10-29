# Related work and contribution boundaries

The focused inherited review has primary PVLDB papers for MillWheel and Dataflow,
DOI bibliographic metadata for Chandy/Lamport and Utting et al., and pinned primary
Debezium/RaftScope repositories. The original verification record is preserved at
`../submission/LITERATURE_VERIFICATION.json`; it is historical evidence, not proof
of a successful retrieval today. No comprehensive novelty search is claimed.

| Work | Appropriate use in candidate | What is not established |
|---|---|---|
| MillWheel, PVLDB 6(11), 1033–1044, 2013 | Persistent state/fault-tolerant streaming context | No reproduction or performance comparison. |
| Dataflow Model, PVLDB 8(12), 1792–1803, 2015, DOI 10.14778/2824032.2824076 | Unordered-input correctness/latency/cost context | No claim this lab solves event-time/window semantics. |
| Chandy/Lamport, TOCS 3(1), 63–75, 1985, DOI 10.1145/214451.214456 | Distinguishes distributed consistent snapshots from one-process JSON restore | No distributed-cut implementation or equivalent guarantee. |
| Utting/Pretschner/Legeard, STVR 22(5), 297–312, 2012, DOI 10.1002/stvr.456 | Established model-based testing context | Bibliographic/abstract verification only in inherited record; no full-text technical comparison. |
| Debezium PostgreSQL docs, pinned d9e8eeb… | Actual connector has LSN-bearing events and restart offsets | LSN is not automatically the model's integer version; multi-source/epoch semantics not implemented. |
| RaftScope, pinned 5b0c10a… | Interactive algorithm visualization precedes this lab | No user-study or superiority claim. |

The candidate removes NoREC: the earlier audit verified metadata/abstract only,
and merely name-checking its reference-engine technique did not substantiate a CDC
comparison. Its original bibliography and verification record remain unchanged.
The candidate adds a pinned public artifact reference; this organizational citation
does not invent individual authorship of Paper 2.

The artifact's defensible contribution is a working, inspectable composition:
stale-delete counterexample; independent canonical state comparison; trace-visible
attempt/restore/replay phases; and expiry probe-order effects. Versions, deduplication,
checkpoints, oracles and visualization are established techniques. There is no
algorithmic novelty, exactly-once, production-performance, or user-learning claim.
Whether this integration is competitive for SIGMOD is an editorial/reviewer judgment,
not established by passing tests. A broader systematic prior-art review and separate
implementation replication remain limitations.
