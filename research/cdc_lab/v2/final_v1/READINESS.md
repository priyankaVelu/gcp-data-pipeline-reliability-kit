# Submission readiness — Paper 2 final preparation v1

**Not ready to submit.** This preparation branch starts from main
`583b90bb5a8bc33b99e4812c4a29399d416beb19`. No conference upload, merge, contact with
chairs, fabricated identity, or overwrite of historical evidence is authorized or
performed. Competitive acceptance is not established by these checks.

## Candidate and audit

- [Revised manuscript](manuscript.tex), [bibliography](references.bib),
  [claim-by-claim audit](CLAIMS.md), [machine audit](CLAIM_AUDIT.json).
- [Reproducibility instructions](README.md), original tested
  [five-minute walkthrough](../WALKTHROUGH.md).
- Production-font PDF and build report: pending the new production CI build; this
  report will be updated with actual paths, page count and font/visual checks.
- All main-tree historical files are SHA-256 protected by `PRESERVATION.json`.
  Earlier V2 source/PDF/build reports are preserved, not presented as current output.

## Verified evidence and actual checks

57 root unit/integration tests passed; frozen V4 pre-result validation and all 15 V5
checks passed. Installed wheel passed nine-scenario smoke tests outside the checkout.
Real Chromium walkthrough passed from that wheel with no JavaScript errors; local
baseline counterexample rendered in 2.342 seconds. This is not a five-minute user study.
The build frontend was unavailable locally, so the wheel was built directly with
installed setuptools 84.0.0; no failed/absent isolated build is counted as passing.

Fresh original runner execution produced 126 principal and 36 bounded rows, all
non-timing fields matching historical run-1. Fresh V2 execution produced 144 principal
and 72 expiry rows in fresh directories, retained under `evidence/`, preserving older committed results. The new audit independently
reduces canonical maxima, replays all 144 retained principal rows, reexecutes all 72
expiry rows and checks every technical field/digest. Correct/incorrect/rejected:
arrival 24/12/12, ID-only 30/6/12, version-aware 36/0/12. No new performance result is
claimed. Historical outcomes, including negative and neutral controls, remain intact.

## Exact blockers requiring resolution before upload

1. **Author metadata absent.** Owner must supply confirmed author list/order,
   affiliations (including institution/city/country as appropriate), email addresses
   and ORCIDs, approve acknowledgments/funding/conflicts and confirm consent. The
   candidate deliberately has no author block; no names, US affiliation or ORCID are
   invented. This violates the inherited nonanonymous-track rule until resolved.
   Adding real authors may alter pagination and requires a new PDF build/review.
2. **Current official CFP and template distribution not independently reachable.**
   The proxy returns CONNECT 403 for official SIGMOD and ACM pages, including an
   escalated retry. `VENUE_EVIDENCE.json` records current attempts; the October 13
   requirements table is inherited, not newly verified. Owner must reconfirm
   [demo CFP](https://2027.sigmod.org/calls_sigmod_demos.shtml),
   [dates](https://2027.sigmod.org/calls_papers_important_dates.shtml),
   [ACM template](https://www.acm.org/publications/proceedings-template).
   Inherited rules: nonanonymous, sigconf 9pt, US Letter, at most four pages including
   references; January 11, 2027 23:59 AoE; author CMT/ORCID and next-day COI requirements.
   Verify these on the live official sources rather than relying on this summary.
3. **Paper 1 overlap review incomplete.** The actual ACMSE 2027 submitted manuscript,
   author-approved version and submission/status information are absent. Available
   V4/V5 scripts/results overlap thematically in silent failures, independent oracles
   and recovery. Full textual/claim/result overlap, attribution and applicable
   originality/concurrent-submission policies cannot be cleared from code alone.
4. **Portal and author administration incomplete.** Confirm CMT demo-track entry,
   author accounts/ORCIDs/COIs, venue-specific declarations and intellectual-property
   permissions. No DOI/ISBN/conference location/dates or rights notice is fabricated.
5. **Final owner editorial/visual approval.** Review actual production PDF after
   real authors are inserted; confirm contribution is sufficiently distinct and
   persuasive. Broader prior-art review and separately authored replication remain
   methodological limitations. Optional video has not been recorded/hosted; do not
   add a fictitious URL. Decide industry designation only if applicable.

## Review boundaries

The contribution is an inspectable local demonstration of established mechanisms,
not a new CDC algorithm, real connector, durable system, exactly-once guarantee,
cloud-cost/throughput result, or validated learning intervention. Authoritative
versions, stable identities and unbounded current state are assumptions. Only ID
memory is bounded in expiry tests. Preflight ambiguity rejection is not online
conflict detection. Ordered seeds repeat equivalent workloads, not independent
statistical samples. Whole-state equality does not count external side effects.

Paper 1 source missing; all available Paper 1-related V4/V5 artifacts untouched.
Paper 3/QueryGuard lives on other branches and is untouched. Earlier Paper 2 papers,
figures, protocols and results are protected. PR targets main for human review only.
