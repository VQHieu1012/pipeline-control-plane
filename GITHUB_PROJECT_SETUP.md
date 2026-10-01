# GitHub Project Setup

Create a GitHub Project named **Pipeline Control Plane**.

## Fields

### Status
- Backlog
- Ready
- In Progress
- Review
- Verify
- Done
- Blocked

### Priority
- P0
- P1
- P2
- P3

### Type
- Feature
- Bug
- Tech Debt
- Spike
- Documentation

### Phase
- M0 Foundation
- M1 Schema & Discovery
- M2 Flink Planning
- M3 Pipeline Planner
- M4 Provisioners
- M5 Reconciler
- M6 Dynamic CDC
- M7 Rollout & Recovery
- M8 Production Hardening

### Area
- Schema
- Discovery
- Planner
- Kafka
- Kafka Connect
- Flink
- Reconciler
- API
- Persistence
- Operations

### Estimate
- 1
- 2
- 3
- 5
- 8

## Views

1. Kanban — board grouped by Status.
2. Roadmap — grouped by Phase.
3. Current milestone — filter current Phase.
4. Blocked — filter Status = Blocked.

## Initial issues

Create these first:

1. `[M0] Project foundation and governance`
2. `[M0] Establish CI quality gates`
3. `[M1] Define CanonicalSchema V1`
4. `[M1] Define TableSelector and resolved-table diff`
5. `[M1] Implement first source metadata adapter`
6. `[M2] Spike: validate PyFlink planner integration`
7. `[M2] Implement transform schema inference`
8. `[M2] Implement final EXPLAIN validation`
9. `[M3] Define PipelineSpec and PipelinePlan`
10. `[M3] Implement deterministic resource/spec hashing`
