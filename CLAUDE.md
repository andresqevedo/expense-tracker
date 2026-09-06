# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Constitution

This project's governing principles, constraints, and workflow rules live in
[`.specify/memory/constitution.md`](.specify/memory/constitution.md). Read it before
making non-trivial changes, and follow it as the source of truth whenever it
conflicts with general defaults. If the constitution itself needs to change, use
the `speckit-constitution` skill rather than editing it as a normal file.

## Spec-Driven Workflow

This repository uses the [Spec Kit](.specify/) workflow. Features are developed
through the following skills, generally in order:

1. `speckit-specify` — create/update a feature spec
2. `speckit-clarify` — resolve ambiguities in the spec
3. `speckit-plan` — produce the implementation plan
4. `speckit-tasks` — break the plan into ordered tasks
5. `speckit-analyze` — cross-check spec/plan/tasks for consistency
6. `speckit-implement` — execute the tasks
7. `speckit-converge` — reconcile the codebase against spec/plan/tasks

Feature artifacts are stored under `.specify/`.

## Docker Test Workflow

Per Constitution Principle II, tests run against the real PostgreSQL service, not
mocks — so a docker compose stack is brought up for each test run:

```
docker compose up -d --build
docker compose exec app pytest
```

Once the suite passes, stop the stack with `docker compose stop` so no
containers are left running in the background — do NOT use `docker compose
down`, which removes the containers rather than just stopping them. If the
suite fails, leave the stack up so the `db`/`app` containers and logs are
available for debugging — only stop it after a fix produces a passing run.
