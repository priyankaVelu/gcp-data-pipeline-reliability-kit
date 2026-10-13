# CDC Replay Correctness Lab — Paper 2 demonstration artifact

Target: SIGMOD 2027 Demonstrations. Draft for review, not a submission. The official
2027 website returned HTTP 403 during this task; deadlines, page limits, template
and anonymity requirements remain to be verified before submission.

## Audit of the existing demo

Audited main commit `202b7dc59df31ded1e54ed0825ba8f476ac324d6` (merged PR #14).
All 40 existing unittest tests passed before changes. Existing `cdc_demo.py`:
- seeded shuffled input with duplicates, positive integer versions and tombstones;
- whole-stream conflict validation before execution;
- independent batch maximum-version oracle, sharing validation with the processor;
- serialized logical state plus unbounded ID ledger restored from an earlier offset;
- full-stream redelivery and JSON invariants;
- arrival-order baseline whose interruption argument does not influence execution.

Confirmed limitations: no ID-only comparator, no finite ledger study, no durable
storage, fsync, transactional offset commit, external CDC, GUI or real crash test.
The old naive helper does not actually execute lost pre-checkpoint work; the new
suite models attempted work and rollback for all strategies. Existing demo files,
Paper 1 materials, frozen protocols and historical results are unchanged.

## Reproduce

Python 3.10+ and the standard library suffice. Run from repository root:

```sh
python -m unittest discover -s tests -v
python research/test_paper_experiments_v4.py
python research/test_paper_experiments_v5.py
python research/cdc_lab/run.py --output /tmp/cdc-lab-new-run
python -m pipeline_reliability.cdc_demo --seed 7 --checkpoint-after 2 --interrupt-after 5
pdflatex -halt-on-error -output-directory=/tmp research/cdc_lab/manuscript.tex
```

The output directory must not exist. Retained artifacts: `results/run-1/results.json`,
`principal.csv`, `bounded.csv`, and `SHA256.json`. JSON holds arrays and nulls; CSV
stores nested arrays/objects as JSON cells and nulls as empty cells. Boolean CSV
cells are `True`/`False`. The JSON artifact is authoritative for types. Runtime
samples vary on rerun; correctness and workload hashes are deterministic.

Protocol was committed as `f1d14aa` before implementation; first measured run
used `8e91b4b` with no tracked modifications. No external preregistration or
independent replication has occurred. Recovery offsets and counts describe source
attempts, not exactly-once side effects. Manifest hashes cover data artifacts,
not the manifest itself. Runner preserves a failure.json for technical exceptions.

## Observed run (Python 3.12.14)

126 principal rows, 36 bounded rows, five timing samples per observation. Each
principal strategy had six rejected conflict inputs and 36 valid observations:

| Strategy | Correct state | Incorrect state | Nondecreasing-version failures |
| --- | ---: | ---: | ---: |
| Arrival | 6 | 30 | 30 |
| ID-only | 6 | 30 | 30 |
| Version-aware | 36 | 0 | 0 |

All redelivery state-unchanged checks passed, **including incorrect baselines**.
Thus a stable redelivery result is not evidence of correct state. Correctness counts
are synthetic final-state observations, not independent statistical samples or
external-effect guarantees. Duplicate scenario also shuffles arrivals: it is a
compound condition, not an isolated duplicate-only causal comparison.

Local principal median-time ranges across configurations (includes early conflict
rejection): arrival 0.020040–20.123117 ms; ID-only 0.021011–25.376994 ms; version-aware
0.021251–26.441142 ms. These are observed timings on this host, not performance
claims. Rejected rows perform less work and must not be pooled with valid rows for
performance comparisons. Raw samples and configuration-specific medians are retained.

Bounded version-aware state remained unchanged for every tested capacity/seed. At
capacities 0/4/16 the oldest ID was forgotten; at unlimited capacity it was recognized.
Capacity 0 missed the conflicting stale payload. Capacities 4/16 detected it only
because the preceding exact stale redelivery reinserted the identity. Do not infer
that arbitrary old conflicts are detected. ID-only finite ledgers changed final
state on oldest redelivery for all three seeds. Tombstone/state retention remains
unbounded and versions must be authoritative/comparable; no bounded-state or
exactly-once guarantee follows.

## Deterministic counterexample and demo interactions

For key x deliver `(ID=a, version=4, live)` then `(ID=b, version=3, deleted)`.
Arrival and ID-only end at a stale tombstone; version-aware retains live v4.
The distinct IDs show why ID deduplication alone cannot solve ordering. This is
asserted in `test_counterexample_and_tombstones` without seed searching.

Audience walkthrough: inspect events; choose a strategy; compare materialization
to the batch oracle; inspect wrong keys and attempted/recovered counters; change
checkpoint boundaries with the existing demo CLI; open bounded.csv to contrast
state correctness, duplicate recognition and conflict detection. The interaction is
command-line and artifact-based. A graphical side-by-side viewer is proposed work.

## Literature verification and remaining questions

Full text retrieved from the official VLDB host on 2026-10-13:
- Tyler Akidau et al. **MillWheel: Fault-Tolerant Stream Processing at Internet
  Scale**, PVLDB 6(11), 2013, pp. 1033–1044.
  https://www.vldb.org/pvldb/vol6/p1033-akidau.pdf
- Tyler Akidau et al. **The Dataflow Model: A Practical Approach to Balancing
  Correctness, Latency, and Cost in Massive-Scale, Unbounded, Out-of-Order Data
  Processing**, PVLDB 8(12), 2015, pp. 1792–1803.
  https://www.vldb.org/pvldb/vol8/p1792-Akidau.pdf
  Crossref DOI record verified: https://doi.org/10.14778/2824032.2824076

MillWheel discusses persistent state and fault tolerance; Dataflow discusses
out-of-order/event-time processing and correctness tradeoffs. Our single-process
version ordering is not a recreation of either system. Related-work review questions:
which CDC sources provide a comparable version order across delete/reinsert? How
do transactional sinks couple state/identity/source offsets? What retention horizon
permits safe ID expiry? How do tombstone garbage collection and key reuse interact?
What does this demonstration add to existing teaching and differential-testing labs?
These remain questions, not established novelty. Focused reading is not a systematic
literature review. No submitted ACMSE manuscript is changed or reused as this paper.
