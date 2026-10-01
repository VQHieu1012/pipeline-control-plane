# Pipeline Control Plane

Declarative control plane for planning, provisioning, and reconciling CDC pipelines across source databases, Kafka/Kafka Connect, and Apache Flink.

## Why

A long-running CDC pipeline should not be owned by an imperative workflow that repeatedly performs:

```text
create connector
→ wait
→ discover topic/schema
→ create Flink job
→ wait
```

This project models the pipeline as desired state:

```text
PipelineSpec
    ↓
Plan
    ↓
Desired resources
    ↓
Reconcile
    ↓
Actual infrastructure + Conditions
```

## Architecture

```text
User / UI / Airflow
        |
        v
+-------------------+
| Control Plane API |
+---------+---------+
          |
          v
+-------------------+
| Desired State DB  |
|   PostgreSQL      |
+---------+---------+
          |
          v
+-------------------+
|   Reconciler      |
+----+----------+---+
     |          |
     v          v
Kafka /       Kubernetes API
Connect            |
                   v
          Flink Kubernetes Operator
                   |
                   v
              Flink runtime
```

Planning path:

```text
Native DB metadata
       ↓
CanonicalSchema
       ↓
PyFlink Planner
       ↓
validate transform
       ↓
ResolvedSchema
       ↓
PipelinePlan
       ↓
Desired Resources
```

## V1 goals

- discover exact and pattern-matched source tables;
- normalize source metadata into a canonical schema;
- validate Flink SQL transforms without submitting a production job;
- derive Kafka topic, Kafka Connect, and Flink desired specs;
- reconcile desired vs actual state;
- support dynamic onboarding when a new table matches a selector;
- expose precise pipeline/table conditions.

## Documentation

- [Product vision](docs/product/vision.md)
- [V1 scope](docs/product/v1-scope.md)
- [System overview](docs/architecture/overview.md)
- [Pipeline lifecycle](docs/architecture/pipeline-lifecycle.md)
- [Roadmap](docs/project-management/roadmap.md)
- [Kanban workflow](docs/project-management/kanban.md)
- [ADR process](docs/adr/README.md)

## Status

Project foundation / pre-implementation planning.
