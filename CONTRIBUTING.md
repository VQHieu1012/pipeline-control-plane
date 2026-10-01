# Contributing

## Workflow

1. Start from an issue in Ready.
2. Keep WIP within the project limits.
3. Use a focused branch/PR per issue.
4. Include tests with behavioral changes.
5. Update ADR/docs when changing architecture.
6. Move work to Verify after implementation; Done requires acceptance verification.

## Local quality gates

Before a PR:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

## Pull requests

A PR should explain:

- problem;
- solution;
- important design choices;
- validation performed;
- risks/follow-up;
- linked issue.

## Architecture changes

Create or update an ADR when a change affects:

- domain model;
- resource ownership;
- reconciliation semantics;
- schema/type semantics;
- runtime/planner boundaries;
- persistence model.
