# Validation record

Local Python 3.11: 39 QueryGuard tests passed (29 existing, 10 new), 57 root tests
passed, frozen V4 pre-result validation passed, and all 15 V5 pre-result checks
passed. Synthetic CLI/research smoke execution passed; its newly generated output
was moved outside the repository. These are pre-result/regression checks, not new
V4/V5 research measurements.

The measured run retained 1,080 matrix observations plus 36 fixture observations,
with three solver executions per observation, and reproduced every non-timing field
of 216 frozen baseline rows. Independent verification re-enumerates all 180 matrix
optima and checks each selected plan, deterministic replay, bundle marginal
witnesses, mode budgets, CSV/JSON parity, timing validity, hashes and summaries.
The preservation manifest covers all pre-existing tracked files, including Papers
1/2, V4/V5 and historical QueryGuard artifacts. No such file is changed by this PR.

Actual GitHub Actions conclusions are recorded in the pull request after the runs
complete. Skipped or pending workflows must not be read as successful executions.
