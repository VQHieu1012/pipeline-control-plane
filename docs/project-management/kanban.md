# Kanban Workflow

## Board columns

```text
Backlog
  ↓
Ready
  ↓
In Progress
  ↓
Review
  ↓
Verify
  ↓
Done

Blocked = exception state
```

## Meaning

### Backlog

Accepted idea/work, not yet ready to start.

### Ready

Requirements and acceptance criteria are sufficient to implement.

### In Progress

Active implementation or investigation.

### Review

Code/design is awaiting review.

### Verify

Implementation is merged or complete, but acceptance criteria/integration behavior still need verification.

### Done

Acceptance criteria and Definition of Done are satisfied.

### Blocked

Work cannot progress because of a concrete external dependency or unresolved decision.

## WIP limits

For a solo/small-team V1:

- In Progress: max 2
- Review: max 2
- Verify: max 2

Do not start new work when WIP limits are exceeded; finish existing work first.

## Priority

- P0 — correctness/system blocker
- P1 — required for current milestone
- P2 — useful but not milestone-blocking
- P3 — later

## Work types

- Feature
- Bug
- Tech Debt
- Spike
- Documentation

## Definition of Ready

An issue can move to Ready when it has:

- problem statement;
- input/output or observable behavior;
- acceptance criteria;
- known dependencies;
- explicit out-of-scope notes when ambiguity is likely.

## Definition of Done

- implementation complete;
- unit/integration tests as appropriate;
- ruff/mypy/pytest pass;
- failure path considered;
- idempotency test for reconciler logic;
- docs/ADR updated when architecture changes;
- acceptance criteria verified.

## Suggested GitHub Project fields

Create a GitHub Project named **Pipeline Control Plane** with:

- Status: Backlog / Ready / In Progress / Review / Verify / Done / Blocked
- Priority: P0 / P1 / P2 / P3
- Type: Feature / Bug / Tech Debt / Spike / Documentation
- Milestone/Phase: M0–M8
- Estimate: 1 / 2 / 3 / 5 / 8
- Area: Schema / Discovery / Planner / Kafka / Connect / Flink / Reconciler / API / Persistence / Ops

Recommended views:

1. **Kanban** grouped by Status.
2. **Roadmap** grouped by Milestone/Phase.
3. **Current milestone** filtered to active milestone.
4. **Blocked** filtered to Status=Blocked.
