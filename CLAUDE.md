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

1. `speckit-specify`: create/update a feature spec
2. `speckit-clarify`: resolve ambiguities in the spec
3. `speckit-plan`: produce the implementation plan
4. `speckit-tasks`: break the plan into ordered tasks
5. `speckit-analyze`: cross-check spec/plan/tasks for consistency
6. `speckit-implement`: execute the tasks
7. `speckit-converge`: reconcile the codebase against spec/plan/tasks

Feature artifacts are stored under `.specify/`.

## Documentation Style

Em dashes (—) are never allowed in documentation. This applies to README
files, docstrings, inline comments, and any other prose written into this
repository. Use a period, comma, colon, or parentheses instead.

## Docker Test Workflow

Per Constitution Principle II, tests run against the real PostgreSQL service, not
mocks. The `app` service builds the lean `final` Dockerfile stage (no compiler,
no dev dependencies, no test files) and is not equipped to run pytest; a
separate `test` service builds the `test` stage (adds the `dev` extras and
`tests/`) and is gated behind the `test` compose profile so it never starts on
a plain `docker compose up`. It overrides the image's entrypoint to run pytest
directly instead of the `alembic upgrade head` migration `entrypoint.sh`
otherwise runs. That migration targets the dev database, which the test
suite never touches, since `tests/conftest.py` creates and migrates its own
`expense_tracker_test` database independently. Run the whole suite with one
command:

```
docker compose --profile test run --rm --build test pytest
```

`run` starts `db` (waiting for its healthcheck) if it isn't already up, and
propagates pytest's real exit code, unlike `docker compose up`, which reports
success even when the one-shot test container inside it fails. `--rm` cleans
up the test container afterward; `db` keeps running.

Once the suite passes, stop `db` with `docker compose stop` so no containers
are left running in the background. Do NOT use `docker compose down`, which
removes the containers rather than just stopping them. If the suite fails,
leave `db` up so it's available for debugging; only stop it after a fix
produces a passing run.
