# SIGMOD 2027 Demonstrations — official submission requirements

Verified October 13, 2026 from the official conference CFP:
https://2027.sigmod.org/calls_sigmod_demos.shtml
Official deadlines: https://2027.sigmod.org/calls_papers_important_dates.shtml

This replaces the earlier "all requirements unknown" note after the official CFP became accessible via a separate retrieval environment. **Manuscript is still not submission-ready.**

| Requirement | Official rule | Manuscript action |
| --- | --- | --- |
| Track | SIGMOD 2027 Demonstrations | Keep demonstration-centered claims and audience interaction |
| Deadline | Monday, January 11, 2027, 11:59 PM Anywhere on Earth | Submit early; confirm live portal |
| COI deadline | 24 hours after submission deadline (Jan 12 AoE) | Every author declares individual domains and PC conflicts in CMT |
| Acceptance | March 8, 2027 | Informational |
| PDF | Single PDF, US Letter 8.5 x 11 inches | Validate page dimensions |
| Page limit | At most FOUR pages **including bibliography and all other material** | Check built PDF |
| Template | Latest official ACM Proceedings `sample-sigconf.tex` or ACM_SigConf.docx | Obtain official current template from https://www.acm.org/publications/proceedings-template |
| Font | **9 pt**; LaTeX `\\documentclass[sigconf,9pt]{acmart}` | Replace current anonymous/review 10pt declaration; preserve margins and spacing |
| Review | **NOT double-blind** | Include actual author names and affiliations in PDF; remove `anonymous` |
| Authors | Every author has registered CMT account and ORCID | Owner must supply verified metadata; never invent |
| Video | Optional, <=5 minutes, hosted online | If supplied, include URL in proposal abstract; do not fabricate |
| Industry demos | Append `[Industry]` to submission title when opting into industry-demo designation | Confirm whether industry designation is appropriate; do not assume |
| Selection | Intellectual contribution + working system + audience experience | Clearly show interactions, architecture, novel aspects and related work |
| Concurrent work | Review applicable originality and duplicate-submission policies | Compare ACMSE Paper 1 before submission; do not assume independence solely from different title |
| Submission | CMT link from official demonstration CFP | Verify actual demo submission entry is available before final upload |

Additional requirements: demonstrate implemented vs planned features accurately; cite related system publications; follow conference diversity and inclusion writing guidance. Formatting violations can cause desk rejection.

## Outstanding blockers

1. Update `v2/submission/manuscript.tex` to nonanonymous 9pt `sigconf` and add real verified author/affiliation data. No author identity should be invented.
2. Rebuild using current official ACM template and required fonts; check four-page limit **including references**, letter dimensions, and PDF quality.
3. Check actual CMT demonstration-track portal availability, every author's CMT and ORCID registration, and COI declarations.
4. Decide whether to record/host a real five-minute video; include its URL in abstract only if real.
5. Perform substantive overlap and concurrent-submission review against the actual ACMSE 2027 submitted manuscript, which is not in this repository checkout.
6. Expand and verify related work and evaluate whether the demonstration's contribution meets SIGMOD's competitive standard.

Historical PR #15 results and submitted ACMSE Paper 1 remain protected. Do not merge or submit automatically.
