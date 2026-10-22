# Five-minute live demonstration

Run from a clean checkout, Python 3.10+:

```sh
python -m pipeline_reliability.cdc_interactive --port 8765
```

Open http://127.0.0.1:8765 in your browser on the same machine. No authentication,
cloud credentials, package downloads or external front-end resources are required.
The server binds only to loopback. Stop with Ctrl-C. Alternative: install the wheel
and run the same module from outside the repository; the HTML is packaged in Python.

| Time allocation | Reviewer interaction | Expected visible evidence |
| --- | --- | --- |
| 0:00–0:45 | Click **Stale-delete preset** | One key, distinct IDs, live v4 followed by delete v3; arrival replay shows `k0: stale version` |
| 0:45–1:30 | Switch to **ID deduplication only**, click **Run comparison**; then **Version aware**, run again | ID-only remains wrong; version-aware matches canonical live v4 |
| 1:30–2:15 | Use **Next event** or drag the trace-position slider | Inspect before/after state, decision and ledger size; v3 becomes a stale decision under version replay |
| 2:15–3:15 | Select **post recovery redelivery**, 3 keys, checkpoint 4, interruption 8, native order, unlimited capacity | Four discarded attempts, four replayed lost attempts, restored earlier state; version replay matches oracle and redelivery is unchanged |
| 3:15–4:15 | Select **ledger expiry**, 16 keys, checkpoint/interruption 0, capacity 4, online validation | Final state matches, but warning explicitly says injected conflict was not detected |
| 4:15–5:00 | Clear capacity (unlimited), run again; compare **Whole input** preflight mode | Online unlimited ledger detects conflicting ID and stops; global preflight rejects before any replay. Discuss memory and durability assumptions |

These are presenter time allocations, not measured user-study durations. The entire
sequence is asserted through HTTP integration tests and a real Chromium browser.
Browser testing starts the installed wheel outside the checkout, selects/fills real
controls, steps the trace, verifies DOM results and rejects JavaScript errors. The
known-failing preset must render within 60 seconds in the automated browser check.
No claim about audience understanding or usability-study outcomes is made.

Invalid offsets (checkpoint greater than interruption or beyond event count) display
a clear error. Source ordering controls can reverse, shuffle with a seed, or order
by version; changing these is a distinct input treatment. Tombstones/state remain
unbounded even when ID capacity is finite. A conflict-stopped run has no completed
correctness verdict. The expected canonical state remains visible for inspection.
