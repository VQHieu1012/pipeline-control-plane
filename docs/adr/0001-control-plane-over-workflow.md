# ADR-0001: Use a reconciled control plane for long-running CDC pipelines

Status: Accepted

## Context

The existing orchestration model performs a finite sequence such as:

```text
submit Kafka Connect
→ poll RUNNING
→ wait for topic/schema
→ generate Flink DDL
→ submit Flink
→ poll RUNNING
```

This is workable for initial provisioning but couples long-running desired state to an imperative workflow.

## Decision

The project will model a CDC pipeline as durable desired state and use a long-running reconciler to converge actual resources toward that state.

Airflow or other workflow engines may request a pipeline, but they are not the long-term owner of pipeline runtime state.

## Consequences

Positive:

- reconciliation survives process/workflow restarts;
- rollout and drift become explicit;
- dynamic table discovery fits naturally;
- resource status can be aggregated into conditions.

Costs:

- requires durable desired-state persistence;
- requires idempotent resource clients;
- introduces eventual consistency;
- status modeling becomes a first-class design problem.
