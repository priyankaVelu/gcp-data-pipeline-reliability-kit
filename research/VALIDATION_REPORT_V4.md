# Experiment Suite V4 - Post-Run Validation Report

## Status

Post-run validation was completed after preservation of the original V4 results.

The original V4 protocol, implementation, raw results, summary, and failure log remain unchanged.

## Preserved Experiment

- Protocol: `research/EXPERIMENT_PROTOCOL_V4.md`

- Execution commit: `7ef6a1c6728d49ed12693b7ed0dc2d69de7f13d2`

- Results preservation commit: `dcb501f`

- Raw observations: 480

- Principal observations: 180

- Single-fault control observations: 300

- Recorded technical failures: 0

- Python: 3.13.14

- Timing repetitions: 7

## Artifact Integrity

Independent SHA-256 calculation for the raw CSV:

`fa0d0d713e650d244ec001fca2071a0fc26d4f2766919342fcf6c13dfbc3d4e7`

This exactly matches `raw_sha256` recorded in the V4 summary.

The failure artifact contains an empty JSON array (`[]`), consistent with the summary reporting zero technical failures.

## Structural Validation

The raw CSV contains:

- 480 rows and 44 columns.

- 180 principal observations.

- 300 single-fault controls.

- 120 observations for each of S1, S2, S3, and S4.

- 160 observations at each dataset size: 1,000; 10,000; and 100,000.

- No byte-identical duplicate rows.

- No empty cells.

Configuration-key validation found:

- 180 unique principal configurations from 180 principal rows.

- 300 unique control configurations from 300 control rows.

- Zero duplicated principal configuration keys.

- Zero duplicated control configuration keys.

- 60 observations for each isolated fault condition: duplicate, null_key, late, conflict, and recovery.

All rows reference the execution commit above and Python 3.13.14.

## Metric Arithmetic Validation

Seven derived rates were independently recomputed from their stored numerators and denominators across all 480 observations, for 3,360 rate checks.

Results:

- Out-of-bounds rates: 0

- Zero denominators: 0

- Numerator/denominator arithmetic mismatches: 0

## Realized Fault-Count Validation

Duplicate, null-key, and late-event realized counts follow the configured nominal rates.

Conflict injection is constrained by the number of available entities. At the nominal 10% setting, the requested number of conflict records exceeds the number of distinct entities available, so realized conflict counts are capped at the entity count.

Accordingly, the configured percentages should be described as nominal compound-fault intensity settings and accompanied by realized fault counts. The nominal 10% conflict setting must not be interpreted as 10% of rows receiving distinct entity conflicts.

Recovery replay counts are calculated after preceding workload transformations and therefore vary with compound-fault intensity.

## Single-Fault Control Validation

### Duplicate Control

All four strategies suppress ordinary injected duplicate events in the isolated duplicate control:

- state correctness = 1.0

- duplicate leakage = 0.0

- recovery completeness = 1.0

- false rejection = 0.0

- fault detection recall = 1.0

### Null-Key Control

All four strategies reject invalid business-key records.

Across the isolated 5% null-key control:

- invalid-key leakage = 0.0

- recovery completeness = 0.95

- false rejection = 0.05

- fault detection recall = 1.0

State correctness varies because removal of a canonical event affects final state only when the rejected event is relevant to the oracle state for its entity.

### Late-Event Control

Temporal strategies S2 and S4 achieve state correctness 1.0 and stale-state rate 0.0 in the isolated late-event control.

Non-temporal strategies S1 and S3 retain substantial stale state.

This control successfully distinguishes temporal from arrival-order processing.

### Conflict Control

Temporal strategies S2 and S4 achieve state correctness 1.0 and stale-state rate 0.0 in the isolated conflict control.

Non-temporal strategies S1 and S3 produce state correctness 0.0 and stale-state rate 1.0.

This control successfully distinguishes event-time resolution from arrival-order resolution under the implemented conflict construction.

## Recovery-Control Identifiability Defect

The isolated recovery control does not distinguish S1/S2 from S3/S4. All four strategies produce:

- state correctness = 1.0

- duplicate leakage = 0.0

- recovery completeness = 1.0

- false rejection = 0.0

- recovery-related aggregate fault detection contribution = 0

Post-run code inspection identified the mechanism.

Recovery copies are prepended to the workload before their corresponding ordinary records. The replay copy therefore encounters an empty event-ID seen set and is retained. When the corresponding ordinary record is encountered later, common event-ID deduplication suppresses that ordinary record.

Consequently, both non-idempotent-recovery and idempotent-recovery strategies retain one logical copy of the event. The recovery-specific branch cannot produce the intended observable distinction.

Recovery detection is similarly non-identifiable because the replay-tagged record arrives first and is retained; the later discarded record is the untagged ordinary record.

Therefore, V4 does not provide an identifiable empirical test of the preregistered H3 recovery hypothesis. This should not be interpreted as evidence that idempotent recovery has no effect.

No V4 result is altered or excluded because of this finding.

## Fault-Detection Metric Limitation

`fault_detection_recall` is arithmetically correct according to its implementation, but its numerator combines heterogeneous mechanism-specific signals: duplicate suppression, invalid-key validation, temporal handling of late/conflicting records, and recovery replay detection.

Because recovery detection is non-identifiable in V4, aggregate detection recall should not be interpreted as a general anomaly-detection accuracy measure.

Any reporting of this metric should explicitly describe its benchmark-specific definition and limitation.

## Overall Assessment

V4 passes artifact-integrity, execution-completeness, configuration-completeness, arithmetic-consistency, duplicate-control, null-key-control, late-event-control, and conflict-control validation.

V4 has a recovery-control identifiability defect and limitations in the interpretation of aggregate fault-detection recall and nominal conflict intensity.

The preserved V4 artifacts remain valid records of the preregistered execution. The recovery defect was identified only during post-run validation and has not been retroactively corrected.

A subsequent protocol version should correct recovery semantics and freeze the revised experimental design before implementation and execution.
