# QueryGuard — research prototype

**Status: exploratory, not a validated novel algorithm or production system.**

QueryGuard investigates budgeted data-quality check selection with consumer-weighted detection utility and dataset-level shared scan costs. The original milestone below is a small, fully reproducible counterexample; it is not an empirical warehouse benchmark.

## Reproduce

From the repository root (Python 3.10+; no external dependencies):

```bash
python -m unittest discover -s research/queryguard/tests -v
python research/queryguard/proof_of_concept.py
```

The script exhaustively enumerates check subsets, using a **synthetic** budget of 7 cost units. A and B each cover five units and reduce 8 units of modeled consumer risk; C covers twelve units and reduces 12 units of modeled consumer risk. Each standalone check costs 6 units, while A and B together cost 7 because they share a dataset scan.

Coverage-optimal selects C (risk reduction 12); risk-optimal selects A+B (risk reduction 16). This only demonstrates that objectives differ when risk weights differ. It does **not** establish novelty or superiority over risk-weighted baselines.

## Research safeguards

- No client data, production claims, measured BigQuery costs, or fabricated benchmarks.
- The original proof-of-concept utility is additive; it **does not** model overlapping fault detection.
- Costs are synthetic units, not actual BigQuery billing.
- Next: independent fault/consumer incidence matrix, overlap-aware utility, shared-scan calibration, risk-weighted and budget-aware baselines, uncertainty analysis, and real execution-cost measurements.
- Keep Paper 1 (compound-failure reliability) and Paper 2 (CDC replay correctness) distinct; assess publication overlap before submission.


## Overlap-aware consumer-risk extension

The [versioned planner and experiment guide](overlap_v1/README.md) adds explicit
fault-scenario/consumer incidence, union utility, compatible shared-scan groups,
small-instance exact search and three marginal greedy policies. The original
`proof_of_concept.py` and its tests remain unchanged.

```sh
python -m research.queryguard.overlap_v1 --fixture overlap --budget 6
python -m research.queryguard.overlap_v1 --fixture shared_scan_trap --budget 7 --policy risk_aware_greedy
python -m unittest discover -s research/queryguard/tests -v
```

The extension remains synthetic and exploratory. Its retained results include cases
where risk-aware greedy is worse than coverage greedy and a setup-sharing fixture
where every greedy policy is suboptimal. No novelty, warehouse cost calibration,
real-world detection efficacy or universal superiority is claimed.
