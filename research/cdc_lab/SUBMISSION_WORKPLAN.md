# Paper 2 — SIGMOD 2027 demonstration submission workplan

Status: submission preparation only; no venue submission or acceptance. This document does not revise historical results.

## Protected baseline

- PR #15 is merged; the source experiment protocol, retained 126 principal and 36 bounded observations, JSON/CSV, hashes, and manuscript review draft form the Paper 2 baseline.
- Never edit Paper 1's submitted ACMSE manuscript, frozen V4/V5 research, or historical research outputs. Never regenerate results in `research/cdc_lab/results/run-1/`.
- For new experiments use a distinct versioned directory and record commit, seeds, environment, protocols, and hashes.
- Preserve PR #15 baseline in Git history; submit further changes as reviewable PRs without automatic merge.

## Priority 0: venue compliance (blocker before submission)

Verify the official SIGMOD 2027 demonstration CFP and submission portal: exact deadline and timezone, track, page count (including references), ACM template, anonymization, author/ORCID registration, artifact/video requirements, originality and concurrent-submission policies. Capture primary-source links and date checked. If official website is inaccessible, mark unknown and request clarification from chairs; do not claim compliance.

## Priority 1: methodological audit and corrective experiments

1. Verify the original `run.py` counts against the committed JSON/CSV and hash manifest; report actual verification commands.
2. Inspect experiment scenario construction: `duplicates` also shuffles; `delete_reinsert` also shuffles and appends stale updates. Do not present them as isolated causal factors. Add an isolated duplicate-only workload and a genuinely ordered delete/reinsert workload as **new** experimental conditions, without altering original protocol or results.
3. Audit `nondecreasing_version` under checkpoint rollback. Distinguish attempted writes before interruption from committed/recovered writes; avoid combining counters in a way that could be mistaken for committed-state violations.
4. Test independent oracle against hand-authored cases, including stale delete, reinsertion, same-version conflict, duplicate ID with conflicting payload, and expiry of a remembered ID. Explicitly distinguish global input validation from online detection.
5. Add independent rerun instructions and a small provenance/comparison report; keep synthetic model and sample-size limits visible.

## Priority 2: actual interactive demonstration

Build a small standard-library local interactive interface (e.g., a terminal menu or a localhost HTTP server if appropriate), with user-selectable event ordering, strategy (arrival / ID-only / version-aware), checkpoint and interruption offsets, ID ledger capacity, and an event-by-event trace. Display side-by-side materialized states, oracle state, wrong keys, recovery counters, and conflict verdict. It must not imply disk durability, exactly-once guarantees, or production CDC connectivity. Include a five-minute scripted demo with deterministic known-failing example, tested end-to-end.

## Priority 3: manuscript and scholarship

- Revise `research/cdc_lab/manuscript.tex` on this branch only. Use the verified venue template and page rules once confirmed.
- Frame contribution as a reproducible, interactive educational/diagnostic demonstration, not a novel CDC algorithm.
- Explicitly identify assumptions (stable IDs, authoritative comparable per-key versions, retained tombstones, bounded synthetic workloads).
- Expand literature review beyond MillWheel/Dataflow to CDC source ordering contracts, stream fault tolerance, stateful recovery, differential/model-based testing, and prior interactive teaching artifacts. Verify citations from primary publications.
- Include actual interface screenshots/figures, reproducible examples, observed outcomes, threats to validity, and no speculative performance claims.
- Compare overlap with submitted ACMSE Paper 1 before submission; avoid reusing its manuscript/results as new research and comply with concurrent-submission policies.

## Definition of done

- All existing tests and V4/V5 validations pass; new interaction tests pass; GitHub Actions pass.
- New experiments, if any, have independent output directories and preserved negative results.
- Verified CFP compliance checklist with source links; no unknown marked complete.
- Manuscript PDF builds under the verified template and meets the actual page limit.
- Five-minute interactive demo runs from clean checkout, with clear limitations.
- Reviewer checklist explicitly confirms no Paper 1/V4/V5 file modifications.
- No merge or conference submission without user review.
