# GCP Data Pipeline Reliability Kit

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23106610.svg)](https://doi.org/10.5281/zenodo.23106610)

Open-source reliability patterns for production data pipelines on Google Cloud, BigQuery, Apache Airflow / Cloud Composer, and Python.

## Local command-line tool

Install with `python -m pip install .` (Python 3.10+) to use `pipeline-reliability`
for CSV duplicate-key, null-key, freshness, and duplicate-current-record checks.
No cloud credentials are required. See the [five-minute quickstart](docs/cli.md)
for synthetic examples, configuration, JSON output, and exit codes.

## Why this project exists

Production data pipelines fail in predictable ways: incomplete failure context, unsafe backfills, weak data-quality checks, duplicate processing, stale data, and insufficient auditability.

This project turns those recurring problems into small, reusable, vendor-conscious patterns that data engineers can understand, test, and adapt.

The goal is not to provide a full platform. It is to provide practical reference implementations for common reliability problems.

## Initial roadmap

The first release, **v0.1.0 — Production Reliability Foundations**, establishes the initial reliability foundation in three areas:

1. **Metadata-aware Airflow failure callbacks**
   - capture DAG and task context
   - read declared pipeline metadata
   - produce a structured failure record
   - fail visibly when the callback itself encounters an error

2. **Safe backfill patterns**
   - bounded date/time windows
   - dry-run support
   - guardrails against unexpectedly large runs
   - explicit audit metadata

3. **BigQuery data-quality and audit checks**
   - row-count validation
   - freshness checks
   - null-key checks
   - duplicate-key detection
   - duplicate-current-record detection

## Design principles

- Reliability should be designed, not added after incidents.
- Operational metadata should be machine-readable.
- Backfills should be explicit, bounded, and auditable.
- Data-quality assertions should reflect business grain, not merely SQL uniqueness.
- Examples should be understandable without access to proprietary systems.
- All sample datasets and identifiers in this repository are fictional.

## Repository structure

```text
airflow/
  failure_callbacks/
  retry_patterns/
  backfill_patterns/
  audit_logging/

bigquery/
  data_quality/
  freshness_checks/
  duplicate_detection/

examples/
  sample_pipeline/

tests/

docs/
  architecture.md
  design_principles.md
  production_checklist.md
```

## Project status

This project is under active development. **v0.1.0** is the first citable research-software release and is permanently archived on Zenodo.

## Citation

If you use this software in research or practice, cite the archived software release:

**Priyanka Velumani. GCP Data Pipeline Reliability Kit, v0.1.0. Zenodo. https://doi.org/10.5281/zenodo.23106610**

Machine-readable citation metadata is also available in [CITATION.cff](CITATION.cff).

## Who this is for

- Data engineers
- Analytics engineers
- Cloud engineers
- Airflow / Cloud Composer users
- Teams operating BigQuery-based data platforms

## Contributing

Contributions, bug reports, design discussions, and production-use feedback are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0. See [LICENSE](LICENSE).

## Author

Created and maintained by **Priyanka Velumani**.

This is an independent open-source project. It does not contain proprietary employer or client code, data, architecture, or confidential implementation details.
