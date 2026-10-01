# Pipeline Lifecycle

## Planning boundary

Planning must complete before external mutation.

```text
INPUT
  ↓
DISCOVERY
  ↓
SCHEMA
  ↓
FLINK VALIDATION
  ↓
PIPELINE PLAN
----------------- side-effect boundary
  ↓
APPLY / RECONCILE
```

## Table lifecycle

Suggested per-table lifecycle:

```text
DISCOVERED
   ↓
SCHEMA_RESOLVED
   ↓
PLAN_VALID
   ↓
TOPIC_READY
   ↓
FLINK_READY
   ↓
CDC_INCLUDED
   ↓
RUNNING
```

Snapshot/backfill can later introduce:

```text
CDC_INCLUDED
   ↓
SNAPSHOTTING
   ↓
STREAMING
```

## Dynamic table discovery

User intent:

```text
selector = dbo.order_.*
```

Observed set at time T1:

```text
order_2025
order_2026
```

Observed set at T2:

```text
order_2025
order_2026
order_2027
```

Reconciliation computes:

```text
added   = {order_2027}
removed = {}
stable  = {order_2025, order_2026}
```

Only the newly resolved table enters onboarding.

## Shared connector

The user selector remains declarative.

The effective Kafka Connect membership may be expanded by the control plane:

```text
desired selector:
  dbo.order_.*

effective include list:
  dbo.order_2025
  dbo.order_2026
  dbo.order_2027
```

This lets the control plane prepare table-specific resources before enabling CDC for the table.

## Reconciliation rule

A reconcile iteration should do bounded work:

1. read desired state;
2. read relevant actual state;
3. perform at most the required idempotent mutations;
4. persist observed state/conditions;
5. exit.

Never implement long `while status != READY: sleep()` loops inside a reconcile iteration.
