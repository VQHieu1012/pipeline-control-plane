# Roadmap

The project uses capability milestones with explicit exit criteria rather than arbitrary completion percentages.

## M0 — Foundation

Goal: project governance and executable skeleton.

Deliverables:

- product vision;
- V1 scope;
- system overview;
- roadmap;
- ADR process;
- issue/PR templates;
- quality-gate design.

Exit:

- scope is reviewable;
- architecture boundaries are documented;
- first implementation backlog exists.

## M1 — Schema & Discovery

Goal: reliably understand source tables.

Deliverables:

- CanonicalSchema V1;
- TableSelector;
- resolved-table diffing;
- source introspector interface;
- first source adapter.

Exit:

- a real source table can be converted deterministically to CanonicalSchema;
- exact and pattern selection are tested.

## M2 — Flink Planning

Goal: validate transforms without production job submission.

Deliverables:

- PyFlink planner wrapper;
- source table registration;
- transform validation;
- output ResolvedSchema;
- final EXPLAIN validation.

Exit:

- invalid SQL/types fail in planning;
- valid transform yields deterministic output schema.

## M3 — Pipeline Planner

Goal: intent → desired plan.

Deliverables:

- PipelineSpec;
- PipelinePlan;
- dependency graph;
- deterministic spec hashing.

Exit:

- same input produces the same plan;
- no external side effects are required to plan.

## M4 — Provisioners

Goal: materialize individual resources.

Deliverables:

- Kafka topic client;
- Kafka Connect client/spec;
- Flink K8s spec/client;
- dry-run support.

Exit:

- create/read/update/no-op tested per resource.

## M5 — Reconciler

Goal: continuously converge desired and actual state.

Deliverables:

- reconciliation loop;
- conditions;
- retry/backoff;
- observed_generation;
- process-restart recovery.

Exit:

- duplicate reconcile is safe;
- process restart does not lose intent.

## M6 — Dynamic CDC

Goal: onboard future tables matching a selector.

Deliverables:

- periodic discovery;
- resolved-table set diff;
- per-table lifecycle;
- connector membership reconciliation.

Exit:

- a newly created matching table reaches RUNNING automatically.

## M7 — Rollout & Recovery

Goal: controlled updates.

Deliverables:

- generation/spec hash rollout;
- drift handling;
- defined snapshot semantics;
- recovery behavior.

## M8 — Production Hardening

Goal: operable service.

Deliverables:

- metrics;
- audit events;
- locking/HA;
- RBAC/security;
- failure injection;
- runbooks.
