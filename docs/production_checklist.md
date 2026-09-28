# Production Data Pipeline Reliability Checklist

## Ownership and metadata
- [ ] Business owner is declared
- [ ] Technical owner is declared
- [ ] Criticality is declared
- [ ] Runbook or operating guidance exists
- [ ] Expected freshness / SLA is documented

## Failure handling
- [ ] Retries are intentional rather than default-only
- [ ] Final failure produces actionable context
- [ ] Failure-callback errors are surfaced
- [ ] Log and run identifiers are preserved

## Backfills
- [ ] Backfill window is explicit
- [ ] Maximum allowed range is bounded
- [ ] Dry-run / preview behavior exists where practical
- [ ] Parameters are recorded for audit
- [ ] Idempotency or duplicate behavior is understood

## Data quality
- [ ] Required keys are non-null
- [ ] Expected business grain is documented
- [ ] Duplicate-key checks exist
- [ ] Current-record uniqueness is validated where applicable
- [ ] Freshness is validated
- [ ] Source-vs-target reconciliation exists where needed

## Observability
- [ ] Start/end status is recorded
- [ ] Row counts are recorded
- [ ] Failure reason is queryable
- [ ] Pipeline metadata is queryable
- [ ] Operational metrics can be trended
