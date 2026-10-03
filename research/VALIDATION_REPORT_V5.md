# V5 Post-Run Validation Report

## Status

Experiment Suite V5 completed successfully and its raw artifacts were preserved before post-run interpretation.

This report documents validation of the preregistered V5 experiment without altering, relabeling, deleting, or rerunning the preserved observations.

## Provenance

- Protocol: `research/EXPERIMENT_PROTOCOL_V5.md`
- Protocol commit: `d08e8a5`
- Initial implementation/tests commit: `513101365f87ffc65a3bbae5464427e6e9352946`
- Execution commit: `a65b68914ed795ad7f0b7abda6fce0cc64045f6f`
- Untouched-results preservation commit: `7c46bcff65a30ddc7611ecacbc7cd0122133112e`
- Protocol version: 5.0
- Timing repeats per observation: 7

The only change between the initial implementation commit and the execution commit was progress logging intended to make a long local run observable. The experimental constants, workload construction, strategies, metrics, and hypotheses were not changed.

## Preserved artifacts and integrity

Artifacts:

- `research/results/raw/paper-suite-v5-20261003T191556Z.csv`
- `research/results/paper-suite-v5-20261003T191556Z-summary.json`
- `research/results/paper-suite-v5-20261003T191556Z-failures.json`

SHA-256 values calculated before preservation:

- Raw CSV: `faa2fab7e08a2c69204f0925b7b78343200355a34ac4442aca56227f5b8fb8e7`
- Summary JSON: `395bbad5aaa21ea135ab0cc5f16436247b4e021d10e3125991d5b7c40a05ae83`
- Failures JSON: `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`

The summary embeds the same raw CSV SHA-256. The failures artifact is an empty JSON array (`[]`), indicating zero recorded technical failures.

## Matrix validation

The raw CSV contains 480 observations:

- 180 principal compound-failure observations
- 300 isolated single-fault controls
- 120 observations per strategy
- 160 observations per dataset size
- 60 controls for each of duplicate, null-key, late, conflict, and recovery
- 0 duplicate configurations
- 0 primary-rate bound violations
- 5 frozen seeds, each contributing 36 principal observations
- 7 timing repeats for every observation

Dataset sizes are 1,000, 10,000, and 100,000. Principal nominal compound intensities are 1%, 5%, and 10%.

## Recovery identifiability

V5 corrected the recovery-identifiability problem documented for V4.

For isolated recovery controls, the minimum number of already-committed replayed IDs was 250, so the recovery-specific denominator was nonzero in every recovery workload.

Observed recovery behavior:

| Strategy | Already-committed replay behavior | Recovery duplicate-effect rate |
| --- | --- | ---: |
| S1 Minimal | reprocessed | 1.0 |
| S2 Temporal | reprocessed | 1.0 |
| S3 Recovery | suppressed | 0.0 |
| S4 Full | suppressed | 0.0 |

Across sizes, non-idempotent S1/S2 reprocessed 250, 2,500, or 25,000 already-committed replay IDs, while idempotent S3/S4 suppressed those same counts.

Therefore V5 provides an identifiable controlled comparison for the preregistered recovery hypothesis. This is a synthetic benchmark result and is not a claim about universal production recovery behavior.

## Isolated-control validation

### Duplicate replay

All four strategies produced:

- state correctness rate = 1.0
- duplicate leakage rate = 0.0
- invalid-key leakage rate = 0.0
- stale-state rate = 0.0
- recovery completeness rate = 1.0
- false-rejection rate = 0.0

This is consistent with ordinary event-ID deduplication being enabled in all four strategies.

### Null-key corruption

At the 5% isolated-control intensity, all four strategies produced median:

- state correctness rate = 0.95
- invalid-key leakage rate = 0.0
- stale-state rate = 0.05
- recovery completeness rate = 0.95
- false-rejection rate = 0.05

Required-key validation prevents invalid-key leakage, but rejecting corrupted canonical records reduces membership/completeness under the predefined oracle and metric definitions. This should not be described as perfect end-to-end correctness.

### Late arrival

Median isolated late-control results:

| Strategy | State correctness | Stale-state rate |
| --- | ---: | ---: |
| S1 Minimal | 0.404 | 0.596 |
| S2 Temporal | 1.000 | 0.000 |
| S3 Recovery | 0.404 | 0.596 |
| S4 Full | 1.000 | 0.000 |

The matched temporal/non-temporal distinction is observable.

### Temporal conflict

Median isolated conflict-control results:

| Strategy | State correctness | Stale-state rate |
| --- | ---: | ---: |
| S1 Minimal | 0.950 | 0.050 |
| S2 Temporal | 1.000 | 0.000 |
| S3 Recovery | 0.950 | 0.050 |
| S4 Full | 1.000 | 0.000 |

The matched temporal/non-temporal distinction is again observable.

### Recovery replay

Median isolated recovery-control results:

| Strategy | Duplicate leakage | Recovery duplicate-effect rate |
| --- | ---: | ---: |
| S1 Minimal | 1.000 | 1.000 |
| S2 Temporal | 1.000 | 1.000 |
| S3 Recovery | 0.000 | 0.000 |
| S4 Full | 0.000 | 0.000 |

## Principal compound-failure findings

### 1% nominal intensity

Median state correctness:

- S1 Minimal: 0.8104
- S2 Temporal: 0.9896
- S3 Recovery: 0.8104
- S4 Full: 0.9896

Median stale-state rate:

- S1 Minimal: 0.1896
- S2 Temporal: 0.0104
- S3 Recovery: 0.1896
- S4 Full: 0.0104

Median recovery duplicate-effect rate:

- S1/S2: 1.0
- S3/S4: 0.0

### 5% nominal intensity

Median state correctness:

- S1 Minimal: 0.3820
- S2 Temporal: 0.9506
- S3 Recovery: 0.3820
- S4 Full: 0.9506

Median stale-state rate:

- S1 Minimal: 0.6180
- S2 Temporal: 0.0494
- S3 Recovery: 0.6180
- S4 Full: 0.0494

Median recovery duplicate-effect rate:

- S1/S2: 1.0
- S3/S4: 0.0

### 10% nominal intensity

Median state correctness:

- S1 Minimal: 0.2096
- S2 Temporal: 0.8980
- S3 Recovery: 0.2096
- S4 Full: 0.8980

Median stale-state rate:

- S1 Minimal: 0.7904
- S2 Temporal: 0.1020
- S3 Recovery: 0.7904
- S4 Full: 0.1020

Median recovery duplicate-effect rate:

- S1/S2: 1.0
- S3/S4: 0.0

All strategies had invalid-key leakage rate 0.0. Recovery completeness and false rejection tracked the null-key corruption intensity: 0.99/0.01, 0.95/0.05, and 0.90/0.10 respectively.

S4 is not interpreted as universally or perfectly correct. At 10% nominal compound intensity, for example, its median state correctness is 0.898 and recovery completeness is 0.900.

## Runtime findings

Principal median runtime by dataset size:

| Size | S1 Minimal | S2 Temporal | S3 Recovery | S4 Full |
| ---: | ---: | ---: | ---: | ---: |
| 1,000 | 26.9114 ms | 26.9687 ms | 24.4617 ms | 24.3391 ms |
| 10,000 | 278.3611 ms | 279.5281 ms | 250.9786 ms | 253.1196 ms |
| 100,000 | 2935.7239 ms | 2958.1165 ms | 2673.7748 ms | 2696.0656 ms |

Matched principal comparisons across 45 configurations per pair:

| Comparison | Median delta (right - left) | Right slower | Right faster |
| --- | ---: | ---: | ---: |
| S1 -> S2 | +0.7860 ms | 29 | 16 |
| S1 -> S3 | -27.4869 ms | 1 | 44 |
| S2 -> S4 | -26.4085 ms | 1 | 44 |
| S3 -> S4 | +0.7948 ms | 34 | 11 |

The results do not support a simplistic claim that every added reliability control increases runtime. Temporal resolution shows a small positive median runtime difference in the matched comparisons, while idempotent recovery is faster in nearly all matched principal configurations because already-committed replay work is suppressed in this implementation and workload.

Runtime results are local computational measurements, not cloud cost, throughput, latency-SLA, or production performance claims.

## Hypothesis assessment

### H1: control composition affects final-state correctness under compound failures

Supported within the controlled synthetic benchmark.

The temporal/non-temporal compositions produce materially different state-correctness and stale-state outcomes under the same frozen compound workloads. Recovery-aware/non-recovery-aware compositions also produce materially different replay-duplicate outcomes.

### H2: event-time-aware temporal resolution reduces stale-state errors

Supported within the controlled synthetic benchmark.

The direction is observed in both isolated late/conflict controls and compound workloads. Matched comparisons S1 vs S2 and S3 vs S4 isolate the temporal-resolution distinction.

### H3: idempotent recovery reduces replay-induced duplicate effects

Supported within the controlled synthetic benchmark.

V5 uses committed-before-replay semantics with a nonzero already-committed replay denominator. S1/S2 reprocess already-committed replay and show a recovery duplicate-effect rate of 1.0, whereas S3/S4 suppress it and show 0.0.

### H4: compound workloads can produce outcomes not fully characterized by isolated controls

Provisional evidence is consistent with H4, but this report does not elevate that observation beyond what was directly validated.

Compound workloads show combined stale-state, false-rejection/completeness, and recovery-duplicate consequences that are separated in isolated controls. A manuscript claim should quantify isolated-versus-compound differences explicitly and avoid implying statistical interaction unless an appropriate interaction analysis is performed.

### H5: reliability controls can impose measurable local cost and correctness/runtime tradeoffs

Supported only in the broader, directional-caveat sense defined by the observed benchmark.

Measurable matched runtime differences exist. Temporal resolution usually increases local runtime slightly, while idempotent recovery reduces runtime in nearly all matched compound configurations because replay work is avoided. The experiment therefore demonstrates implementation- and workload-specific computational tradeoffs, not a universal overhead law.

## Protocol-compliance and reporting limitations

### Missing per-fault resulting-correctness-violation field

The V5 protocol requested, per fault class where meaningful:

- faults injected
- faults recognized by control
- faults correctly contained
- resulting correctness violation count

The V5 CSV includes injected, recognized, and contained fields for each fault class, but it does not include a separate per-fault `resulting_correctness_violation_count` field.

This is a reporting-schema deviation from the preregistered protocol. The preserved primary correctness metrics remain available and were validated, but the missing field must be disclosed rather than retroactively added to the V5 raw artifact.

### Late/conflict recognition semantics

For isolated late and conflict controls:

- `late_faults_recognized = 0`
- `late_faults_contained = 0`
- `conflict_faults_recognized = 0`
- `conflict_faults_contained = 0`

for all strategies.

Temporal S2/S4 nevertheless produce lower stale-state errors because event-time state resolution is a processing semantic rather than an explicit anomaly-recognition mechanism in this implementation.

Therefore the manuscript must not claim that S2/S4 explicitly detected or recognized late/conflicting events based on these fields. Correctness outcomes should be described using the state-correctness and stale-state metrics.

### Heterogeneous fault accounting

No single aggregate of the fault-recognition fields should be presented as general anomaly-detection accuracy or general fault-detection recall. Fault classes have different semantics and denominators.

### Duplicate leakage denominator under compound workloads

The compound duplicate-leakage rate includes predefined duplicate/recovery opportunities in its denominator. Its decrease as nominal compound intensity rises must not be interpreted as higher fault intensity improving reliability. The manuscript should describe the exact denominator and rely on recovery-specific metrics when discussing restart/replay behavior.

### Synthetic benchmark boundary

V5 is a deterministic local synthetic benchmark. It does not establish:

- production cloud reliability
- real-world incident frequency
- availability or SLA effects
- enterprise financial impact
- vendor superiority
- universal architectural superiority
- universal runtime overhead

Causal language is limited to the controlled manipulations represented by this benchmark.

## Relationship to V4

V4 is preserved unchanged.

V4's recovery manipulation was non-identifiable because replay records could appear before not-yet-committed originals while ordinary event-ID deduplication remained enabled across all strategies. Replay copies could therefore substitute for originals without exposing the intended recovery distinction.

V5 prospectively changed the recovery semantics to establish an explicit committed boundary and replay IDs already committed before interruption. The V5 recovery control then produced the preregistered strategy distinction.

V4 results are not deleted, altered, or relabeled.

## Validation conclusion

V5 passes the major post-run integrity, matrix, bounds, reproducibility, isolated-control, recovery-identifiability, and matched-strategy checks performed in this audit.

The experiment also contains a documented reporting-schema deviation: the absence of a separate per-fault resulting-correctness-violation-count field. Late/conflict recognition fields represent no explicit anomaly-recognition mechanism and must not be interpreted as detection recall.

These limitations should remain visible in the manuscript and artifact documentation.

Subject to explicit treatment of those limitations and a rigorous literature/novelty review, the preserved V5 evidence is suitable to advance to manuscript preparation. No additional experiment version should be created solely to improve, simplify, or beautify the observed findings.
