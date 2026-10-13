# SIGMOD 2027 Demonstrations: compliance status

Checked 2026-10-13. Status: **blocked; not submission-ready**.

Authoritative CFP requested: https://2027.sigmod.org/ . The environment proxy returns
HTTP 403 on CONNECT. No 2026 deadline, page limit or review policy is assumed to apply
to 2027. The official submission portal could not be discovered or verified.

| Requirement | Verified status | Required action |
| --- | --- | --- |
| Track name and eligibility | User-specified target only | Read official 2027 Demonstrations CFP |
| Deadline/timezone | Unknown | Confirm exact date/time/timezone from CFP/portal |
| Page limit and whether references count | Unknown | Confirm before cutting final manuscript |
| Required template/options | Unknown | Confirm ACM class, size and review settings |
| Anonymous review policy | Unknown | Confirm; anonymous preview is provisional |
| Author/ORCID/registration | Unknown | Confirm portal requirements |
| Artifact/video rules | Unknown | Confirm mandatory/optional content and lengths |
| Originality/concurrent submission | Unknown | Check official policy and overlap with ACMSE Paper 1 |
| Accessibility/metadata/TAPS production | Unknown | Check current ACM and venue instructions |

No requirement above is marked complete. No chairs were contacted: the task does
not authorize sending messages on the user's behalf. The owner should obtain the
CFP or clarification from chairs if access remains blocked.

## Template provenance and current PDF

The revised source is a new version at `v2/submission/manuscript.tex`, based on the
original Paper 2 manuscript but preserving its bytes. ACM `acmart` upstream release
v2.20 was retrieved through the GitHub API from
https://github.com/borisveytsman/acmart/tree/v2.20 . The upstream README states that
GitHub development versions are not production releases; using a release tag here
is a provisional review build, **not verification of the official venue template**.
The class is unmodified; its standard fallback is used when ACM fonts are unavailable.
CTAN access (https://mirrors.ctan.org/macros/latex/contrib/acmart.zip) and the ACM
production guidance site also return proxy 403. Libertine/Inconsolata/NewTX fonts
are missing locally. Any fallback-font build is explicitly an incomplete ACM preview.

Before submission: obtain the officially required production template, install its
required fonts, verify every CFP rule above, supply confirmed authors/ORCIDs, verify
Paper 1 overlap and rights/anonymity rules, and rebuild/check the final PDF. Never
infer readiness from a successful LaTeX compile or an arbitrary four-page length.
