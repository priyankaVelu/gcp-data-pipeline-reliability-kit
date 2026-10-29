# Available-source overlap review

The actual submitted ACMSE 2027 Paper 1 manuscript/PDF is absent from main. All
tracked .tex/.pdf files were inventoried: only original Paper 2, V2 Paper 2 and this
new candidate were found. No statement of clearance or non-overlap is warranted.

Available frozen V4/V5 protocols and runners were reviewed without alteration:
`research/EXPERIMENT_PROTOCOL_V4.md`, `EXPERIMENT_PROTOCOL_V5.md`,
`run_paper_experiments_v4.py`, and `run_paper_experiments_v5.py`. They share substantive
concepts with Paper 2: canonical pre-injection oracles, deterministic synthetic
faults, composed temporal/recovery controls, isolated and compound conditions,
final-state correctness and local timing. V5 explicitly models already-committed
identities followed by recovery replay; V4's recovery identifiability issue is
documented by the frozen V5 protocol. Do not present these shared methods as newly
invented by Paper 2.

Paper 2's inspected implementation focuses instead on three pedagogical replay
policies, authoritative integer versions, stale-delete/reinsert examples,
request-local event traces and a GUI, rollback of attempted work to a logical JSON
snapshot, reverse redelivery, and online FIFO identity expiry/probe order. Its
126/36 and 144/72 row matrices are separate artifacts from V4/V5. These differences
do not prove sufficient separation from the submitted paper.

Owner must provide the exact submitted source/PDF, authorship, submission status
and any camera-ready/related versions. Compare text, figures, tables, claims,
protocols and reused results; cite and disclose related work appropriately and
review both venues' originality/concurrent-submission policies. Add any necessary
cross-citation only after bibliographic/status details are verified; none is
invented here. Paper 1 remains untouched. Other research (including QueryGuard) is outside this main
snapshot and its branch/history is untouched.

A read-only inventory of all 23 remote branch trees found no .tex/.pdf/.bib/.docx manuscript outside research/cdc_lab. See evidence/PAPER_SOURCE_INVENTORY.json. No branch ref other than this preparation branch was changed.
