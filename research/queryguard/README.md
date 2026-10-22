# QueryGuard — research prototype

**Status: exploratory, not a validated novel algorithm or production system.**

QueryGuard investigates budgeted data-quality check selection with consumer-weighted detection utility and dataset-level shared scan costs. This first milestone is a small, fully reproducible counterexample; it is not an empirical warehouse benchmark.

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
- The current utility is additive; it **does not** model overlapping fault detection.
- Costs are synthetic units, not actual BigQuery billing.
- Next: independent fault/consumer incidence matrix, overlap-aware utility, shared-scan calibration, risk-weighted and budget-aware baselines, uncertainty analysis, and real execution-cost measurements.
- Keep Paper 1 (compound-failure reliability) and Paper 2 (CDC replay correctness) distinct; assess publication overlap before submission.
