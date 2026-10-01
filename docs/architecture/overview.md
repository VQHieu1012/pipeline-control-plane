# System Overview

## Control plane vs data plane

The project is a control plane.

Kafka Connect and Flink remain the data plane.

```text
Control Plane
  ├─ plan
  ├─ persist desired state
  ├─ apply
  └─ reconcile

Data Plane
  ├─ Kafka Connect
  ├─ Kafka
  └─ Flink
```

## Components

### API

Accepts intent, persists desired state, and exposes status.

It must not keep an HTTP request open while infrastructure becomes ready.

### Source adapters

Discover tables and normalize source metadata into CanonicalSchema.

### CanonicalSchema

Platform-owned schema representation:

```text
Flink-compatible logical type
+ native source metadata
+ keys / nullability
+ semantic hints
```

### Flink planner

Uses PyFlink as the Flink-compatible SQL planning frontend.

Responsibilities:

- register logical source/sink tables;
- parse and validate transform SQL;
- infer output ResolvedSchema;
- perform final EXPLAIN validation.

It does not submit the production job.

### Pipeline planner

Pure planning logic:

```text
PipelineSpec + resolved metadata
             ↓
        PipelinePlan
```

Equivalent input should produce equivalent desired specs/spec hashes.

### Desired-state persistence

PostgreSQL stores:

- PipelineSpec;
- generations;
- resolved tables;
- canonical schemas;
- desired resource specs/hashes;
- observed status;
- conditions;
- reconciliation history as required.

### Reconciler

Long-running controller:

```text
desired
  vs
actual
  ↓
create / update / observe / no-op
```

Repeated execution must be safe.

### External controllers

- Kafka/operator → topic lifecycle;
- Kafka Connect → connector/task lifecycle;
- Flink Kubernetes Operator → Flink lifecycle.

The pipeline reconciler aggregates their status rather than reimplementing them.

## Ownership model

A connector may be shared across multiple tables.

```text
Connection / TableSelector
          |
          v
    KafkaConnector
          |
     +----+----+
     |         |
     v         v
 Table A     Table B
   |           |
   + topic     + topic
   + schema    + schema
   + Flink     + Flink
```

Connector membership is selector/connection scoped.

Topic, canonical schema, and Flink resource lifecycle are table scoped.

## Conditions

Prefer Kubernetes-style conditions:

- SourceReachable
- TablesResolved
- SchemaResolved
- TopicReady
- ConnectorReady
- FlinkPlanValid
- FlinkReady
- Ready

Each condition should contain:

- status;
- reason;
- message;
- observed_generation;
- last_transition_time.
