# Governance-Aware Recovery Contracts — preregistered local protocol v1

Status: proposed methodology; local synthetic validator only. No GCP experiments, production observations, or cloud correctness claims.

## Question and hypothesis
Can a pipeline have a correct final row multiset while violating schema or governance metadata expectations? Hypothesis: row-only validation can miss metadata discrepancies. This experiment tests validator detection, not Dataform defects.

## Independent oracle and invariants
Specify the expected snapshot independently of the observed recovered snapshot. Compare (1) exact row multisets with canonical JSON representation, (2) schema descriptors, and (3) column governance descriptors including data policies, governance tags and separately listed row access policies. Fail closed on missing sections. Report each dimension independently and require all to pass. Row order is immaterial; duplicate multiplicity is material. Synthetic policy identifiers do not represent actual GCP resources.

## Prespecified scenarios
A: unchanged snapshot (all pass).
B: same rows, missing governance policy (governance fails).
C: schema type change (schema fails).
D: duplicate row (data fails).
E: missing governance section (contract fails).
F: reordered rows (all pass).

## Execution
Run locally: `cd research/governance_contracts && python -m unittest discover -v`; then `python validator.py`.
No third-party dependencies, cloud credentials, or billing required.

## Cloud validation deferred
Dataform documentation describes `preserveGovernanceControls` for supported data policies and governance tags with Core >=3.0.62. It does not automatically restore row access policies, and it does not support legacy policy tags. Column renames/removals and partition changes have documented limitations. Before integration tests, capture before/after BigQuery INFORMATION_SCHEMA metadata, use an isolated project, and preregister cost and permission constraints.

Sources:
- https://docs.cloud.google.com/dataform/docs/create-tables
- https://docs.cloud.google.com/dataform/docs/release-notes/
- https://docs.cloud.google.com/bigquery/docs/information-schema-columns

## Threats to validity
This validator compares synthetic snapshots and cannot prove cloud metadata persistence, actual enforcement, or real restart behavior. Governance comparison uses literal identifiers; an integration oracle must normalize and independently verify identities and effective policies. Schema lists are order-sensitive by design. No novelty, performance, or GCP failure claims.

## Preservation
Additive files only. Existing Paper 1, V4/V5, and CDC replay research are unchanged. Do not merge before review.
