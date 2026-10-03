# Experiment Protocol V5: Identifiable Compound-Failure Reliability Evaluation

## Status

This document defines the preregistered protocol for Experiment Suite V5.

The protocol must be reviewed and committed before implementation of the V5 experiment runner and before any V5 result is observed.

V5 is a methodological successor to V4. V4 results remain preserved unchanged.

Post-run validation of V4 identified a recovery-control identifiability defect: replay records were prepended before their originals while ordinary event-ID deduplication remained active across all strategies. A replay copy could therefore substitute for its original without creating observable duplicate leakage, preventing the experiment from distinguishing recovery-idempotent and non-idempotent strategies.

V5 corrects that experimental design problem prospectively.

No V5 result may be used to modify the hypotheses, primary metrics, strategy definitions, workload matrix, exclusion rules, or analysis rules defined here.

## Research Question

How do different compositions of validation, deduplication, event-time resolution, and idempotent recovery controls affect data-pipeline correctness under isolated and interacting synthetic failure conditions, and what local computational cost is associated with those controls?

## Experimental Contribution

V5 evaluates a reproducible methodology combining:

- an independent correctness oracle constructed before fault injection;

- deterministic multi-class synthetic fault injection;

- explicit committed-state and restart semantics for recovery;

- matched reliability-control compositions;

- isolated-fault controls;

- compound-failure workloads;

- explicit decomposition of correctness failures;

- deterministic seeds and reproducibility metadata;

- machine-readable result artifacts; and

- correctness-versus-local-computational-cost analysis.

The experiment does not claim that deduplication, event-time processing, validation, checkpoint recovery, or idempotency are individually novel concepts.

The contribution being evaluated is the experimental methodology and the evidence produced by applying these controls systematically under matched deterministic workloads.

## Hypotheses

### H1 — Control Composition

Different compositions of reliability controls will produce different final-state correctness outcomes under compound-failure workloads.

### H2 — Temporal Resolution

Strategies using event-time-aware temporal resolution will reduce stale-state errors caused by late-arriving and conflicting events relative to otherwise comparable non-temporal strategies.

### H3 — Idempotent Recovery

Under a checkpoint/restart workload in which some event identities have already been committed before replay, strategies implementing idempotent recovery will reduce replay-induced duplicate effects relative to otherwise comparable non-idempotent strategies.

### H4 — Fault Interaction

Compound-failure workloads can produce correctness outcomes that are not completely characterized by corresponding isolated single-fault controls.

### H5 — Correctness-Cost Tradeoff

Additional reliability controls can impose measurable local computational cost, creating observable correctness-versus-runtime tradeoffs within the synthetic benchmark.

Failure to support any hypothesis is a valid experimental outcome and must be reported.

## Strategy Definitions

Four principal strategies are evaluated.

### S1 — Minimal

Controls:

- ordinary event-ID deduplication: enabled;

- required-key validation: enabled;

- event-time-aware temporal resolution: disabled;

- idempotent recovery against already committed event identities: disabled.

### S2 — Temporal

Controls:

- ordinary event-ID deduplication: enabled;

- required-key validation: enabled;

- event-time-aware temporal resolution: enabled;

- idempotent recovery against already committed event identities: disabled.

### S3 — Recovery

Controls:

- ordinary event-ID deduplication: enabled;

- required-key validation: enabled;

- event-time-aware temporal resolution: disabled;

- idempotent recovery against already committed event identities: enabled.

### S4 — Full

Controls:

- ordinary event-ID deduplication: enabled;

- required-key validation: enabled;

- event-time-aware temporal resolution: enabled;

- idempotent recovery against already committed event identities: enabled.

The strategy definitions must not change after V5 result observation.

## Canonical Dataset

For each dataset size and seed, generate a deterministic canonical event stream.

Frozen dataset sizes:

- 1,000 events;

- 10,000 events;

- 100,000 events.

Frozen seeds:

- 1301;

- 2609;

- 3911;

- 5209;

- 6521.

Each canonical event must contain at least:

- event_id;

- entity_id;

- business_key;

- event_ts;

- value; and

- fault metadata used only for experimental accounting.

Canonical event IDs must be unique.

The number of logical entities must be deterministic for each dataset size.

## Independent Correctness Oracle

The correctness oracle must be constructed from the canonical dataset before any fault is injected.

The oracle must contain at least:

- the set of valid canonical event identities;

- the expected valid logical membership;

- the expected latest state for every entity according to canonical event time; and

- the expected entity set.

Fault-injected data must never be used to construct or repair the oracle.

The oracle implementation should remain logically separate from the strategy-processing implementation so that strategy behavior does not define its own correctness target.

## Fault Classes

V5 evaluates the following fault classes.

### Duplicate Replay Fault

Duplicate copies of selected observable events are introduced deterministically.

The realized number of duplicate copies must be recorded.

### Null-Key Fault

Selected canonical events have the required business key replaced with null.

The realized number of null-key mutations must be recorded.

### Late-Arrival Fault

Selected events are displaced from canonical arrival order while retaining their original event timestamps.

The realized number of late-arriving events must be recorded.

### Temporal Conflict Fault

Conflicting events are introduced for selected logical entities.

Conflict intensity is defined at the entity level.

For a requested conflict intensity `r`:

`target_conflict_entities = min(entity_count, round(entity_count \* r))`

or an equivalent deterministic integer rule frozen in implementation tests before result generation.

Each selected entity receives one conflicting event.

The result artifact must report both:

- nominal conflict intensity; and

- realized conflicting-entity count.

The paper must not describe conflict intensity as a percentage of physical rows unless it is explicitly calculated as such.

### Recovery Replay Fault

Recovery must model a committed-state boundary.

Recovery processing is divided into explicit phases.

#### Phase A — Pre-Checkpoint Processing

A deterministic prefix of the canonical/faulted workload is processed before interruption.

The identities successfully committed during this phase are recorded as `committed_event_ids`.

The committed logical state is retained.

#### Phase B — Interruption

Processing stops at the frozen checkpoint boundary.

No synthetic correctness metric is calculated by pretending that the interrupted workload is already complete.

#### Phase C — Restart and Replay

After restart, a deterministic subset of events that includes identities already present in `committed_event_ids` is replayed.

The replayed events are then followed by the remaining post-checkpoint workload according to the frozen recovery construction.

For strategies without idempotent recovery, replayed records whose identities were already committed are permitted to be processed again as replay input.

For strategies with idempotent recovery, replayed records whose identities already exist in the committed identity set must be recognized and suppressed as recovery replays.

This committed-before-replay ordering is mandatory.

A replay copy must not merely replace an original record that has not yet been committed.

## Recovery Identifiability Invariant

Before any V5 result run is permitted, deterministic tests must demonstrate that the recovery-only workload is capable of distinguishing the recovery-control dimension.

At minimum, on a small deterministic fixture:

- a non-idempotent recovery strategy must exhibit at least one observable replay-induced duplicate effect or equivalent predefined recovery correctness violation; and

- the corresponding idempotent strategy must suppress that effect while preserving expected logical membership.

This is an experimental-design test, not a hypothesis test.

If this invariant fails, the V5 experiment must not be executed.

## Compound-Fault Intensities

Frozen nominal compound-fault intensity settings:

- 1%;

- 5%;

- 10%.

For each workload, nominal intensity and realized counts must both be recorded.

Different fault classes may use different denominators when required by their semantics.

Therefore, the manuscript must describe 1%, 5%, and 10% as nominal compound-fault intensity settings rather than implying that every fault class modifies the same percentage of physical rows.

## Checkpoint and Replay Parameters

Frozen checkpoint fraction:

`0.50`

Frozen replay fraction:

`0.50`

The exact deterministic integer rounding behavior must be implemented once, tested before execution, and recorded in the experiment metadata.

## Principal Experiment Matrix

For every combination of:

- 3 dataset sizes;

- 5 seeds;

- 3 nominal compound-fault intensities; and

- 4 strategies;

execute one principal correctness observation.

Expected principal observations:

`3 × 5 × 3 × 4 = 180`

The same frozen fault-injected workload for a dataset-size/seed/intensity configuration must be supplied to all four strategies.

## Single-Fault Controls

Single-fault controls are required for:

- duplicate;

- null-key;

- late arrival;

- temporal conflict; and

- recovery replay.

Single-fault controls use a frozen 5% intensity where percentage intensity is applicable.

Recovery-only controls use the frozen checkpoint and replay fractions.

For every dataset size and seed, each single-fault condition is evaluated under all four strategies.

Expected control observations:

`3 × 5 × 5 × 4 = 300`

Expected total observations:

`180 + 300 = 480`

## Primary Correctness Metrics

### State Correctness Rate

Fraction of oracle entities whose final materialized state exactly matches the independent event-time oracle.

### Duplicate Leakage Rate

Replay- or duplicate-induced excess logical occurrences divided by the predefined duplicate denominator.

The implementation must preserve enough provenance to distinguish ordinary duplicate faults from recovery replay effects when reporting diagnostic metrics.

### Invalid-Key Leakage Rate

Invalid required-key records surviving validation divided by the number of injected invalid-key records.

### Stale-State Rate

Fraction of oracle entities whose final state is present but differs from the expected latest event-time state because of stale or incorrect temporal resolution.

### Recovery Completeness Rate

Fraction of expected valid canonical logical membership present after recovery completes.

Recovery completeness measures missing expected membership. It must not be used as the sole measure of replay idempotency.

### False-Rejection Rate

Fraction of expected valid canonical identities incorrectly absent from the final processed logical membership.

## Recovery-Specific Metrics

V5 must report recovery behavior separately from general duplicate behavior.

At minimum record:

- recovery_replay_count;

- already_committed_replay_count;

- recovery_replays_suppressed;

- recovery_replays_reprocessed;

- recovery_duplicate_effect_count; and

- recovery_duplicate_effect_rate.

The exact denominator for `recovery_duplicate_effect_rate` must be the number of replayed identities that had already been successfully committed before interruption.

This denominator must be non-zero for every recovery workload.

## Fault Handling and Detection Metrics

V5 must not present one heterogeneous aggregate as general anomaly-detection accuracy.

For each fault class, record mechanism-specific counts where meaningful:

- faults_injected;

- faults_recognized_by_control;

- faults_correctly_contained; and

- resulting_correctness_violation_count.

Recognition and containment are distinct concepts.

For example, an event may be handled correctly because of deterministic processing semantics without constituting explicit anomaly detection.

If an aggregate benchmark-specific coverage measure is calculated for exploratory analysis, it must be labeled as such and must not be described as general fault-detection recall or anomaly-detection accuracy.

## Runtime Measurement

Correctness and runtime measurement should be separated where practical.

Frozen timing repetitions per strategy/workload:

`7`

Report at minimum:

- median runtime in milliseconds; and

- mean runtime in milliseconds.

Dataset generation, oracle construction, and fault injection must be excluded from timed strategy processing.

All strategies within a matched configuration must receive the same frozen workload.

Timing order must be deterministic or otherwise frozen before execution.

No timing observation may be removed because it is inconvenient or unfavorable.

## Reproducibility Metadata

Every result row or associated machine-readable artifact must preserve enough metadata to identify:

- protocol version;

- experiment kind;

- fault condition;

- dataset size;

- seed;

- nominal intensity;

- realized fault counts;

- checkpoint fraction;

- replay fraction;

- strategy;

- timing repetitions;

- implementation commit SHA; and

- Python version.

The experiment runner must generate machine-readable raw results and summary artifacts.

A technical-failure artifact must also be generated even when no technical failures occur.

## Pre-Result Test Gate

Before executing the full V5 experiment, automated tests must validate at least:

- frozen matrix constants;

- deterministic canonical generation;

- oracle independence;

- deterministic fault injection;

- realized fault accounting;

- strategy definitions;

- all five single-fault controls;

- committed-before-replay recovery ordering;

- non-zero already-committed replay denominator;

- recovery identifiability invariant;

- conflict entity-denominator semantics;

- metric numerator/denominator arithmetic;

- metric bounds;

- expected principal configuration count;

- expected control configuration count;

- reproducibility metadata; and

- output schema.

The full experiment must not be run until the pre-result test gate passes.

Passing tests must not depend on observing the full V5 experimental results.

## Technical Failure and Exclusion Rules

An observation may be excluded only for a genuine implementation or runtime failure that prevents the predefined observation from being produced correctly.

Every such failure must be preserved in the machine-readable failure artifact.

Observations must not be excluded because:

- a hypothesis is unsupported;

- a strategy performs worse than expected;

- S4 does not outperform another strategy;

- runtime is unexpectedly high or low;

- a metric is unfavorable;

- a seed produces an unusual but valid outcome; or

- the result complicates the intended narrative.

If a methodological defect is discovered after execution, the affected results must remain preserved and the defect must be documented.

## Analysis Plan

The analysis must include all valid principal configurations.

For each strategy, dataset size, and nominal intensity, summarize the primary correctness metrics across the five frozen seeds.

Analyze isolated controls separately from compound-failure workloads.

Compare matched compound and isolated conditions where interpretation is valid.

Report realized fault counts alongside nominal intensity.

Recovery results must include the recovery-specific metrics and must distinguish replay recognition, replay containment, duplicate effects, and missing expected membership.

Temporal results must distinguish late-arrival and conflict behavior.

Runtime analysis must use the frozen timing repetitions and emphasize median runtime while retaining mean runtime.

Variation across seeds must not be hidden.

Unexpected or unfavorable findings must be reported.

## Interpretation Boundaries

V5 is a deterministic synthetic local benchmark.

Results may support statements about behavior within the tested synthetic workloads and strategy definitions.

Results must not be represented as direct measurements of:

- production cloud reliability;

- distributed-system availability;

- real-world incident frequency;

- enterprise business impact;

- vendor-specific service reliability; or

- universal superiority of one architecture.

Causal language must be limited to experimental manipulations supported by the controlled design.

Observed experimental results, interpretation, and external literature must be clearly distinguished in the manuscript.

## Relationship to V4

V4 remains part of the reproducibility record.

Its post-run validation identified that the recovery manipulation did not provide an identifiable test of H3 because recovery replay records could substitute for not-yet-committed originals under common event-ID deduplication.

V5 changes recovery semantics prospectively by introducing an explicit committed-state boundary and already-committed replay population.

V4 observations must not be silently altered, deleted, or relabeled as V5 observations.

V5 results must be stored in separate versioned artifacts.

## Amendment Rule

After this protocol is committed, the following are frozen before V5 result observation:

- research question;

- hypotheses;

- strategy definitions;

- dataset sizes;

- seeds;

- nominal intensities;

- checkpoint fraction;

- replay fraction;

- principal metrics;

- recovery-specific metric definitions;

- oracle semantics;

- principal experiment matrix;

- control matrix;

- timing repetitions;

- exclusion rules; and

- analysis principles.

A genuine implementation defect discovered before execution may be corrected with a documented commit while preserving the protocol's experimental meaning.

A genuine methodological defect requiring a protocol change must be documented explicitly before execution.

No amendment may be made because preliminary or final results are favorable, unfavorable, weak, surprising, or inconsistent with a hypothesis.

## Publication Rule

A valid V5 experiment does not require every hypothesis to be supported.

If the protocol is implemented faithfully, the pre-result test gate passes, the experiment executes without an unresolved methodological defect, and post-run validation confirms artifact and metric integrity, the results become eligible for manuscript analysis regardless of whether they support the hypotheses.

The next default phase after a valid V5 is manuscript preparation rather than creation of another experiment version solely to improve the findings.
