# Paper 2 final preparation, version 1

This is a new candidate revision of `../submission/manuscript.tex` from main commit
`583b90bb5a8bc33b99e4812c4a29399d416beb19`. Earlier manuscripts, PDFs, protocols,
results and Papers 1/3 are unchanged. Nothing is submitted or merged.

Start with [READINESS.md](READINESS.md), [CLAIMS.md](CLAIMS.md), and
[LITERATURE.md](LITERATURE.md). Owner author/affiliation/ORCID metadata and the actual
submitted Paper 1 source are unavailable; no identities or affiliations are invented.
A candidate with no author block is not ready for a nonanonymous submission.

Reproduction from repository root (Python 3.10+, no cloud credentials):

```sh
python -m unittest discover -s tests -v
python research/test_paper_experiments_v4.py
python research/test_paper_experiments_v5.py
python research/cdc_lab/v2/final_v1/audit.py
python research/cdc_lab/run.py --output /tmp/new-baseline
python research/cdc_lab/v2/verify.py --original research/cdc_lab/results/run-1 --reproduced /tmp/new-baseline --report /tmp/new-comparison.json
python research/cdc_lab/v2/run.py --output /tmp/new-isolated
python -m pipeline_reliability.cdc_interactive --port 8765
```

Fresh output paths are required. `evidence/` retains the actual new baseline/V2 executions, exact non-timing comparison, and local test/browser logs. Existing V2 [walkthrough](../WALKTHROUGH.md) contains
presenter time allocations, not a measured usability study. Browser test:
`node tests/cdc_browser_smoke.cjs` with Playwright and Chromium; see V2 README for
installed-wheel environment variables. No remote frontend resources are needed.

Production PDF build requires a full TeX installation, Libertine, Inconsolata and
newtxmath (no Latin Modern fallback), plus pdfinfo/pdffonts/pdftotext and the generic TeX dependency `binhex.tex`
(Debian/Ubuntu `texlive-plain-generic`). Obtain unmodified
`acmart.dtx`, `acmart.ins`, `ACM-Reference-Format.bst` from upstream commit
`10d6d082e522c4034022f38437019ba75589456b` (latest listed tag v2.20 at audit time),
verify against the preserved `../submission/TEMPLATE_PROVENANCE.json`, and run
`latex acmart.ins` in that directory. Then:

```sh
python research/cdc_lab/v2/final_v1/build.py --tex-directory /path/to/acmart --output /tmp/new-production-build
```

The new `Paper 2 final candidate` workflow installs production fonts and runs the
same build. Build rejects >4 pages, non-Letter paper, undefined citations, bitmap or
unembedded fonts, overfull boxes, and known placeholder strings. Author absence is
reported as a blocker, not filled with fabricated metadata. No margins, spacing,
font-size or bibliography compression is used to defeat the page limit. The final
visual figure/citation review must be recorded separately from automated checks.

The production CI job runs only for same-repository PRs (or explicit dispatch). Its
contents-write permission is used solely to publish an unreferenced evidence Git
blob when the normal artifact-download endpoint is blocked. `package_build.py`
packages only generated manuscript build files and the build-driver log, never
environment variables or credentials. The workflow does not update refs, merge,
or submit anything. The resulting PDF/report are reviewed and committed to this
preparation branch by the operator.

The candidate uses acmart's documented `pbalance=true` option for last-page column
balancing. The default `balance` path produced a persistent 1.292pt output-box
overflow even after prose editing. This selects the class-supported balancing
implementation; it does not change body size, margins or spacing. Five pdfLaTeX
passes plus BibTeX allow its cross-run layout to converge. Earlier failed checks
are recorded rather than represented as passing builds.
