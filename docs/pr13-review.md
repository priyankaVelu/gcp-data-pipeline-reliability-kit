# PR #13 review summary

## Changes

The installable `pipeline-reliability` CLI checks local CSV or fictional synthetic
input for duplicate keys, null keys, stale timestamps, and duplicate current
records. This revision adds optional `--strict` completeness enforcement to both
duplicate checks. Default duplicate behavior remains unchanged: empty keys are
excluded from duplicate counting. Strict mode fails on empty or whitespace-only
components anywhere in the input, including non-current historical rows.

`--no-strict` overrides a configured `strict: true`; CLI keys, source, thresholds,
and reference timestamps take precedence over JSON configuration. Invalid strict
configuration types and invalid reference times produce structured errors.
Blank `--now` no longer silently falls back to the wall clock. Duplicate results
add `strict` and `invalid_key_rows` while preserving existing count fields.

Adds a strict configuration example, documents selection/completeness semantics,
and extends CI with reusable installed-wheel checks outside the checkout.

## Actual validation

Executed on Python 3.12.14:

- All 35 unittest tests passed (19 original, 16 CLI tests).
- V4 pre-result validation passed.
- All 15 V5 pre-result checks passed.
- Source distribution and wheel built successfully; wheel built from the sdist.
- Reinstalled the built wheel and ran nine CLI scenarios outside the repository:
  default/strict duplicate checks, configuration override, null validation,
  freshness, invalid reference timestamp, and missing-column errors.
- Installed package imported from the virtual environment, not the checkout.
- `pip check` reported no broken requirements.
- `git diff --check` passed.

Regression coverage includes composite/whitespace keys, historical rows, malformed
CSV quoting and field counts, duplicate/empty headers, missing columns for every
command, malformed/naive timestamps, configuration source and option precedence,
and JSON envelopes/exit codes. Frozen research files and historical results are
unchanged. A pre-existing untracked synthetic result is intentionally excluded.

## Limitations and remaining risks

- CSV processing loads input into memory; large-file streaming is not implemented.
- Duplicate comparisons trim whitespace and remain case-sensitive. Literal `NULL`
  is a string. Custom null markers are not supported.
- Strict duplicate-current checks require completeness in historical rows too;
  callers must choose this policy intentionally.
- JSON fields added to duplicate results may require adjustment for consumers that
  reject unknown properties. Empty datasets still return the documented failure
  with `reason: empty_dataset` rather than duplicate metrics.
- Only Python 3.12 was exercised locally. The configured 3.10/3.12/3.13 GitHub CI
  matrix has not been verified from this environment.
- Live cloud integrations and full experiment matrices were not run. No
  performance, adoption, or production-readiness claims are made.

Human review is required; this PR must remain unmerged by the agent.
