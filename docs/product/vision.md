# Product Vision

## Problem

Provisioning a CDC pipeline requires coordination across source metadata, Kafka Connect, Kafka topics, Schema Registry, Flink SQL, and the Flink Kubernetes Operator.

Imperative orchestration is suitable for bounded workflows but is a poor owner for long-running desired state. Pipelines need continuous reconciliation, explicit dependency modeling, and durable status.

## Vision

Build a declarative CDC Pipeline Control Plane that turns user intent into a validated, reproducible desired state and continuously reconciles that state with runtime infrastructure.

A user describes:

- source connection;
- table selector: exact or pattern;
- optional Flink SQL transform;
- sink;
- operational/runtime options.

The control plane derives and manages:

- resolved tables;
- canonical schemas;
- Kafka topics;
- Kafka Connect connector membership;
- Flink source/sink DDL;
- validated Flink SQL plans;
- Flink job specs;
- pipeline conditions and rollout state.

## Product principles

1. Declarative over imperative.
2. Plan before side effects.
3. Schema is planning-time metadata, not a side effect of the first CDC event.
4. Shared connector where appropriate, per-table lifecycle where necessary.
5. Reconciliation is idempotent.
6. Runtime-specific lifecycle remains delegated to the runtime/operator.
7. Every generated spec and status transition is inspectable.
8. A process restart must not lose control-plane intent.

## Target users

- platform/data engineers operating managed CDC;
- internal services provisioning data pipelines;
- workflow systems that should request pipelines rather than own runtime state.

## V1 success criteria

A user can create a pipeline intent and the system can:

1. inspect matching source tables;
2. normalize metadata into CanonicalSchema;
3. validate a Flink SQL transform without starting a production job;
4. derive desired Kafka, Connect, and Flink specs;
5. apply supported resources;
6. reconcile desired and actual state;
7. discover a new table matching an existing selector;
8. expose conditions explaining why a pipeline/table is not ready.
