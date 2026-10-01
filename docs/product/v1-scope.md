# V1 Scope

## In scope

### Source discovery

- source connection validation;
- exact table selection;
- regex/pattern table selection;
- selector → resolved table reconciliation;
- adapter model for SQL Server, MySQL/MariaDB, and PostgreSQL.

### Canonical schema

Flink-compatible logical types plus:

- native source type;
- precision / scale / length;
- nullability;
- PK / unique keys;
- relevant vendor metadata;
- semantic hints.

### Flink planning

- PyFlink TableEnvironment;
- transform SQL validation;
- output ResolvedSchema inference;
- final `EXPLAIN INSERT INTO ... SELECT ...` validation;
- no production job submission from the planner.

### Desired resources

- KafkaTopicSpec;
- KafkaConnectSpec / effective table membership;
- Flink job specification;
- dependency graph.

### Reconciliation

- durable desired state;
- idempotent create/read/update;
- retry transient failures;
- conditions and observed generation;
- recovery after process restart.

### Dynamic CDC

For `dbo.order_.*`:

1. resolve current matching tables;
2. plan resources per table;
3. provision required table resources;
4. activate the table in effective CDC membership;
5. detect future matching tables and repeat.

## Out of scope for V1

- web UI;
- Kubernetes CRD/operator frontend;
- non-Flink runtimes;
- fully automatic schema-evolution rollout;
- multi-region active/active;
- sophisticated backfill orchestration;
- generic workflow engine;
- billing/quota management;
- multi-tenant authorization.

## V1 happy path

```text
PipelineSpec
    ↓
Resolve TableSelector
    ↓
ResolvedTable[]
    ↓
Inspect native metadata
    ↓
CanonicalSchema
    ↓
Flink Planner
    ├─ validate transform
    ├─ infer output schema
    └─ final EXPLAIN validation
    ↓
PipelinePlan
    ├─ KafkaTopicSpec
    ├─ KafkaConnectSpec
    └─ FlinkJobSpec
    ↓
Persist desired state
    ↓
Reconciler
    ↓
Actual resources + Conditions
```

## Required failure scenarios

V1 is not complete until tests cover:

- source DB unavailable;
- topic already exists;
- Kafka Connect unavailable;
- connector exists with drift;
- Flink operator unavailable;
- Flink job fails/restarts;
- reconciler killed and restarted;
- duplicate reconcile;
- new table appears after pipeline is running.
