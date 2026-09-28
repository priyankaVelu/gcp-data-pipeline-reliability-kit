# Design Principles

## 1. Reliability metadata is configuration
Criticality, ownership, runbook references, and operational expectations should be machine-readable rather than existing only in documentation.

## 2. Assertions should represent business meaning
A technically unique composite key is not automatically the correct business grain. Checks should reflect what downstream consumers are promised.

## 3. Failure handling must fail visibly
A broken callback or notification path should never silently disable operational routing.

## 4. Backfills need guardrails
Backfills should require explicit scope, make large ranges visible, and support dry-run or validation modes where possible.

## 5. Auditability is a feature
Pipelines should make it possible to answer what ran, when, with which parameters, how many records moved, and what failed.

## 6. Examples must be reproducible
Public examples should use synthetic data and minimal dependencies so engineers can understand behavior without access to a private platform.
