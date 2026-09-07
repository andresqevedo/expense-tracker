# 🏦 Expense Tracker

A small server-rendered web app for tracking personal expenses: register/login,
record expenses, view monthly totals by category, and compare actual spend
against a per-category budget.

This is a portfolio project built to demonstrate a spec-driven development
workflow (Spec Kit) end-to-end: from a written feature spec through planning,
task breakdown, and implementation, on top of a real, Dockerized FastAPI +
PostgreSQL stack.

## Features (MVP)

- **Register / log in**: email + password auth, JWT session cookie
  (HS256, 24h expiration).
- **Add an expense**: amount, category, date (must be today), optional
  description.
- **List expenses**: a user's own expenses, most recent first.
- **Monthly totals by category**: expenses for a selected month, summed
  per category.
- **Budget vs. actual**: set a monthly budget per category and see actual
  spend, the difference, and whether the category is under, at, or over
  budget.

Full behavioral detail (acceptance scenarios, edge cases, and functional
requirements) lives in
[`specs/001-expense-tracker-mvp/spec.md`](specs/001-expense-tracker-mvp/spec.md).

## Tech Stack

- **Backend**: FastAPI, async SQLAlchemy 2.0, asyncpg
- **Database**: PostgreSQL 16, schema managed exclusively via Alembic
  migrations
- **Auth**: JWT (python-jose) + bcrypt password hashing (passlib)
- **Templates**: Jinja2, server-rendered HTML (no frontend framework/SPA)
- **Packaging**: uv-locked dependencies (`uv.lock`), multi-stage Docker build
- **Tests**: pytest + pytest-asyncio + httpx, run against the real
  PostgreSQL service (no SQLite, no mocked DB)

These constraints (real Postgres in dev and test, migrations-only schema
changes, async-only DB access, Docker as the only required host dependency,
no committed secrets) are not just conventions: they're enforced by this
repo's [constitution](.specify/memory/constitution.md).

## Running the app

Prerequisites: Docker + Docker Compose. No other host dependency is required.

```bash
cp .env.example .env   # fill in real values; .env is gitignored
docker compose up --build
```

This starts `db` (PostgreSQL) and `app` (FastAPI). The `app` container runs
`alembic upgrade head` on boot, creating the schema and seeding the 7 fixed
expense categories. The app is then reachable at `http://localhost:8000`.

## Running tests

Tests run in a dedicated `test` service (built from the `test` Dockerfile
stage, which includes dev dependencies and the `tests/` directory; the
`app` service's `final` image intentionally excludes both). The `test`
service is gated behind the `test` Compose profile so it never starts on a
plain `docker compose up`, and it runs pytest directly against its own
`expense_tracker_test` database rather than the dev migration entrypoint.

```bash
docker compose --profile test run --rm --build test pytest
```

`run` starts `db` if it isn't already up (waiting for its healthcheck) and
propagates pytest's real exit code. Once the suite passes, stop `db` with
`docker compose stop` (not `down`, which would remove the container) so
nothing is left running in the background.

## Project layout

```
app/                   FastAPI application
  models/               SQLAlchemy models (user, expense, category, budget)
  routers/               Route handlers (auth, expenses, budgets, summary)
  schemas/                Pydantic request/response schemas
  security/               JWT + password hashing
  templates/, static/    Jinja2 templates and CSS
alembic/                Database migrations
tests/                  pytest suite (runs against real Postgres)
specs/                  Spec Kit feature artifacts (see below)
.specify/               Spec Kit workflow config, templates, constitution
```

## Spec-Driven Development with Spec Kit

This project is built using [Spec Kit](.specify/), a workflow where features
are specified, planned, and broken into tasks *before* implementation, and
the codebase is later reconciled back against those artifacts. The governing
rules for how code in this repo must be written (testing order, database
usage, migrations, async boundaries, Docker as the source of truth, and
secret handling) are captured once in
[`.specify/memory/constitution.md`](.specify/memory/constitution.md) and
apply to every feature.

Each feature moves through a fixed sequence of skills, each producing a
committed artifact under `specs/<feature>/`:

1. **`speckit-specify`**: Turns a natural-language feature description into
   a structured spec: prioritized user stories, acceptance scenarios, edge
   cases, and functional requirements. Produces `spec.md`.
2. **`speckit-clarify`**: Asks a small number of targeted questions to
   resolve ambiguity in the spec (e.g. exact category list, decimal
   precision rules, JWT expiration) and records the answers directly in the
   spec's Clarifications log, so decisions are traceable to a session/date
   rather than lost in chat history.
3. **`speckit-plan`**: Translates the clarified spec into an implementation
   plan: architecture, data model, and route contracts. Produces `plan.md`,
   `data-model.md`, and `contracts/`.
4. **`speckit-tasks`**: Breaks the plan into an ordered, dependency-aware
   task list. Produces `tasks.md`.
5. **`speckit-analyze`**: A non-destructive cross-check across spec, plan,
   and tasks for consistency and coverage gaps before any code is written.
6. **`speckit-implement`**: Executes `tasks.md` in order, writing the actual
   application code (and, per the constitution, a failing test before each
   route's implementation).
7. **`speckit-converge`**: After implementation, compares the real codebase
   back against spec/plan/tasks and appends any remaining unbuilt work as
   new tasks, so drift between what was specified and what was built doesn't
   silently accumulate.

The current feature's full artifact set (spec, plan, data model, route
contracts, tasks, quickstart validation steps, and requirements checklist)
is under
[`specs/001-expense-tracker-mvp/`](specs/001-expense-tracker-mvp/). Start
there (`spec.md`) to see the requirements this MVP was built against, and
[`quickstart.md`](specs/001-expense-tracker-mvp/quickstart.md) for the manual
end-to-end validation scenarios used to confirm each user story.
