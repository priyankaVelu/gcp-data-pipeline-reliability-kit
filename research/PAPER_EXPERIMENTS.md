# Paper Experiment Suite v1

This suite performs controlled, deterministic **baseline vs reliability-control** experiments using only generated synthetic data.

## Scenarios

1. Duplicate replay: baseline retains duplicates; controlled path applies deterministic deduplication.
2. Null business key: baseline performs no validation; controlled path detects invalid keys.
3. Bounded backfill: baseline processes the full input; controlled path restricts processing to the declared interval.
4. Stale data: baseline performs no freshness assertion; controlled path measures age against a fixed threshold.

These baseline definitions are deliberately minimal controls, not claims about typical production systems.

## Default matrix

Dataset sizes: 1,000; 10,000; 100,000 rows. Seeds: 101, 202, 303, 404, 505. Fault rate: 1%.

This produces 120 observations (4 scenarios x 2 variants x 3 sizes x 5 seeds).

## Run

From the repository root:

    python research/run_paper_experiments.py

For a quick smoke test:

    python research/run_paper_experiments.py --sizes 100 1000 --seeds 101 202

The runner prints the exact paths of a timestamped raw CSV and JSON summary. Do not edit those files manually.

Generate a Markdown table from the JSON summary:

    python research/analyze_paper_results.py research/results/<summary-file>.json

## Interpretation rules

Runtime is measured with `perf_counter_ns` and is useful for within-environment exploratory overhead comparisons. It must not be generalized to BigQuery, Dataflow, Composer, or other managed-cloud performance.

Correctness and detection outcomes are defined by injected synthetic faults. A baseline marked incorrect means it lacks the specific control being tested; it does not mean all real-world baseline pipelines behave this way.

Preserve every run, including unexpected or unfavorable results. Record failed runs rather than silently deleting them.
