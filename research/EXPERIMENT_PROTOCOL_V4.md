# Experiment Protocol v4: Compound-Failure Stress Evaluation

**Status:** Pre-registered repository protocol. Freeze this specification before implementing or executing the v4 experiment.

## 1. Purpose

V4 evaluates how compositions of pipeline reliability controls behave when several failure classes interact. V2 and V3 remain component-level evidence; V4 is an interaction/stress experiment.

This experiment is a deterministic, synthetic, single-process Python study. It does **not** measure BigQuery, Dataflow, Composer/Airflow, network, distributed-storage, or managed-cloud performance.

## 2. Research question

How do different compositions of reliability controls affect final-state correctness, fault containment, recovery completeness, and local computational cost when multiple data-pipeline failures interact?

## 3. Hypotheses fixed before execution

- **H1:** Control composition affects final-state correctness under compound failures.
- **H2:** Temporal resolution primarily affects stale-state errors arising from late and conflicting events.
- **H3:** Idempotent recovery primarily affects duplicate leakage and recovery correctness following interrupted processing.
- **H4:** Interacting fault types can produce outcomes not fully characterized by corresponding isolated-fault experiments.
- **H5:** Additional reliability controls impose measurable local computational cost, creating a correctness-cost tradeoff.

No hypothesis may be rewritten after results are observed merely to match the observed outcome.

## 4. Independent correctness oracle

For each seed and dataset size, generate a canonical logical dataset and its expected final entity state **before fault injection**.

The oracle is independent of every evaluated strategy. No strategy defines its own correctness criterion.

The canonical state must specify, for each business entity:
- valid business key;
- canonical event identity;
- event-time ordering;
- expected latest valid value/state; and
- expected exactly-once logical membership after recovery.

Fault injection is applied only after this oracle has been materialized in memory.

## 5. Failure model

Compound workloads may contain all of the following:

1. **Duplicate replay** — previously observed logical events are replayed.
2. **Null business keys** — selected observable records lose their required business key.
3. **Late/out-of-order arrival** — selected events arrive in an order different from canonical event time.
4. **Conflicting updates** — multiple updates for an entity can disagree, so arrival order and event-time order may imply different final states.
5. **Interrupted/replayed processing** — processing is interrupted at a defined checkpoint and a portion of input is replayed during recovery.

Fault parameters must have causal meaning and must be stored separately:
- `duplicate_rate`
- `null_key_rate`
- `late_rate`
- `conflict_rate`
- `replay_fraction`
- `checkpoint_fraction`

Do not use a generic `fault_rate` as a label for a variable that does not causally control the relevant fault.

## 6. Evaluated strategies

All strategies are plausible control compositions rather than deliberately malformed algorithms.

| Strategy | Deduplicate | Validate keys | Event-time resolution | Idempotent recovery |
| --- | --- | --- | --- | --- |
| S1 Minimal | Yes | Yes | No | No |
| S2 Temporal | Yes | Yes | Yes | No |
| S3 Recovery | Yes | Yes | No | Yes |
| S4 Full composition | Yes | Yes | Yes | Yes |

The implementation must use the same canonical workload for all four strategies within a configuration.

## 7. Principal experimental matrix

Fixed principal matrix:

- dataset sizes: **1,000; 10,000; 100,000**
- deterministic seeds: **1301, 2609, 3911, 5209, 6521**
- compound-fault intensity levels: **1%, 5%, 10%**
- strategies: **S1, S2, S3, S4**
- timing repetitions per observation: **7**

This yields:

`3 sizes × 5 seeds × 3 intensity levels × 4 strategies = 180 principal observations`

Correctness results are deterministic for a fixed configuration. Timing is repeated seven times and summarized with the median; the arithmetic mean may also be retained as descriptive metadata.

### 7.1 Compound intensity mapping

For the principal compound matrix, intensity `r` controls:
- `duplicate_rate = r`
- `null_key_rate = r`
- `late_rate = r`
- `conflict_rate = r`

The recovery parameters are fixed rather than mislabeled as fault rates:
- `checkpoint_fraction = 0.50`
- `replay_fraction = 0.50`

If rounding is required, the implementation must use a deterministic rule and record the realized injected counts.

## 8. Single-fault controls

Run matched single-fault controls for the same sizes and seeds at the **5%** rate for duplicate, null-key, late-arrival, and conflicting-update faults, plus a recovery-only condition using the fixed checkpoint/replay fractions.

These controls are diagnostic. They are used to compare isolated failures with the compound 5% condition and to investigate H4. They must not replace or be mixed into the 180-observation principal matrix.

## 9. Outcome metrics

### 9.1 Primary metric: final-state correctness

`state_correctness_rate = entities_matching_oracle / oracle_entities`

An entity matches only when its final logical state equals the independent canonical oracle.

### 9.2 Error decomposition

Record at minimum:

- **duplicate_leakage_rate** — unintended duplicate logical events remaining after processing, relative to relevant expected logical events.
- **invalid_key_leakage_rate** — injected invalid-key records surviving when they should be rejected.
- **stale_state_rate** — entities whose final value differs from the oracle because an older/conflicting state prevailed.
- **recovery_completeness_rate** — expected logical state successfully restored following interruption/replay.
- **false_rejection_rate** — valid logical records/entities incorrectly removed or rejected.
- **fault_detection_recall** — detected injected faults divided by detectable injected faults, with numerator and denominator retained.

For every rate, persist the underlying counts so the metric can be independently recomputed.

### 9.3 Computational-cost metric

Record local single-process Python runtime for each strategy/configuration:
- `runtime_ms_median`
- optionally `runtime_ms_mean`
- `timing_repeats = 7`

Runtime is a local computational-cost measurement only. It must not be represented as cloud-platform throughput, latency, or production performance.

## 10. Execution-order controls

To reduce systematic timing bias:
- construct/freeze the workload before timing strategy execution;
- exclude workload generation and fault injection from strategy runtime;
- use the same immutable logical workload for all strategies in a configuration;
- execute correctness outside or separately from repeated timing when practical;
- if strategy execution order is varied, derive that order deterministically from the configuration/seed and record it.

No warm-up or timing observation may be discarded unless a pre-specified technical failure criterion applies.

## 11. Pre-specified validity and exclusion rules

A configuration is valid only if:
- the canonical oracle is generated successfully;
- injected fault counts match deterministic configured/realized rules;
- every strategy receives equivalent input;
- all required metric denominators are defined;
- repeated execution with the same seed produces identical non-timing outputs.

An observation may be excluded only for an implementation/runtime failure that prevents the configured experiment from being executed (for example, uncaught exception or corrupted output artifact). Exclusions must be retained in a machine-readable failure log with configuration and reason.

A result may **not** be excluded because correctness is low, runtime is unfavorable, a hypothesis fails, or S4 does not outperform another strategy.

## 12. Analysis plan fixed before results

Report:
1. all principal configurations, not only favorable results;
2. correctness and error decomposition by strategy, size, and intensity;
3. median local runtime by strategy and size/intensity;
4. matched comparisons between the 5% compound condition and the 5% isolated-fault controls;
5. variation across deterministic seeds;
6. counts as well as percentages;
7. unexpected and unfavorable findings.

The paper must distinguish:
- results directly observed in this synthetic experiment;
- interpretations/inferences;
- claims supported by prior literature.

Do not infer managed-cloud performance or production reliability from these local experiments.

## 13. Reproducibility metadata

Every raw observation must include:
- schema/protocol version;
- Git commit SHA;
- Python version;
- dataset size;
- seed;
- all causal fault parameters;
- strategy;
- realized injected-fault counts;
- raw metric numerators/denominators;
- derived rates;
- timing repetitions and timing summary.

The summary artifact must include:
- generation timestamp;
- experiment configuration;
- observation count;
- source commit SHA;
- SHA-256 digest of the raw CSV.

## 14. Protocol freeze and amendments

After this protocol is committed, hypotheses, primary metrics, oracle semantics, principal strategies, seeds, sizes, intensity levels, and exclusion rules are frozen for the initial v4 run.

If a genuine design or implementation defect is discovered:
1. do not silently edit the frozen protocol;
2. document the defect;
3. create a versioned amendment explaining the change and its reason;
4. distinguish pre-amendment runs from post-amendment runs.

No amendment may be made solely to obtain a more favorable result.

## 15. Interpretation boundary

V4 is designed to evaluate a reproducible methodology for pipeline-correctness controls under deterministic synthetic failures. It does not claim that idempotency, event-time processing, validation, or checkpoint recovery are themselves novel algorithms.

The intended research contribution to evaluate is the combined methodology: an independent correctness oracle, deterministic multi-class fault injection, plausible control compositions, explicit error decomposition, reproducible evidence artifacts, and correctness-versus-local-cost analysis.
