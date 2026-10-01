# Architecture Decision Records

Use ADRs for decisions that materially affect architecture, semantics, operability, or long-term coupling.

## Naming

```text
NNNN-short-title.md
```

Example:

```text
0001-control-plane-over-workflow.md
```

## Template

```markdown
# ADR-NNNN: Title

Status: Proposed | Accepted | Superseded | Rejected

## Context

## Decision

## Alternatives considered

## Consequences

## Follow-up
```

## When an ADR is required

Examples:

- canonical schema/type-system choice;
- PyFlink planner vs direct Calcite;
- PostgreSQL desired state vs Kubernetes CRD;
- table selector expansion semantics;
- connector sharing model;
- state/snapshot/rollout semantics.
