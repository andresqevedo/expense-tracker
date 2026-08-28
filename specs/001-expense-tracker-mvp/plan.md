# Implementation Plan: Expense Tracker MVP

**Branch**: `001-expense-tracker-mvp` | **Date**: 2026-08-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-expense-tracker-mvp/spec.md`

## Summary

A single-user-per-account expense tracker: visitors register and log in with
email/password, logged-in users record expenses (amount, category, date =
today, optional description), view their expense list, view monthly
per-category totals, and set/view a per-category monthly budget compared
against actual spend. Delivered as a server-rendered FastAPI application
(Jinja2 + plain CSS) backed by PostgreSQL via async SQLAlchemy, with schema
managed exclusively through Alembic migrations and the whole stack run via
Docker Compose, per the project constitution.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), Alembic, Jinja2,
Pydantic v2, python-jose (or PyJWT) for JWT, passlib[bcrypt] for password
hashing, asyncpg as the PostgreSQL driver

**Storage**: PostgreSQL 16, run via Docker Compose

**Testing**: pytest, pytest-asyncio, httpx.AsyncClient (ASGITransport)
against the real PostgreSQL instance (Constitution Principle II — no
SQLite/in-memory/mocked DB in tests)

**Target Platform**: Linux server container (Docker Compose), accessed via
browser

**Project Type**: Web application — server-rendered single backend service
(no separate frontend project; Jinja2 templates are served by the FastAPI
app itself)

**Performance Goals**: No throughput/latency target specified by the spec;
standard interactive web-app responsiveness applies (per spec Assumptions).
SC-002 (add expense confirmed in <30s) is a UX/task-completion measure, not
a server-side latency budget.

**Constraints**: Must run entirely via `docker compose up --build` with no
host dependency beyond Docker (Constitution Principle V); all DB access
async (Principle IV); all schema changes via Alembic (Principle III);
secrets only via environment variables loaded from `.env`, which stays
gitignored (Principle VI).

**Scale/Scope**: MVP for individual personal use; no explicit user-count or
data-volume target. Data model must comfortably support a single user's
full expense history (assume low thousands of rows) with no pagination
requirement specified.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check                                                                                                                                                         | Result |
|---|---------------------------------------------------------------------------------------------------------------------------------------------------------------|---|
| I. Test-First Development | Plan requires a failing pytest test committed before each route's implementation; tasks.md (next phase) will sequence tests before implementation per route   | PASS |
| II. Real Database, No Shortcuts | Tests run via httpx.AsyncClient against the app wired to the real PostgreSQL 16 service in Docker Compose; no SQLite/mock substitution planned                | PASS |
| III. Migrations Are the Only Schema Change Path | All tables (users, categories, expenses, budgets) created via Alembic migrations; `Base.metadata.create_all` will not be used                                 | PASS |
| IV. Async All the Way Down | SQLAlchemy 2.0 async engine/session + asyncpg driver; all FastAPI route handlers and dependencies use `async def` and `AsyncSession`                          | PASS |
| V. Docker Is the Source of Truth | `docker-compose.yml` defines the `app` and `db` services; app has no host-only setup step                                                                     | PASS |
| VI. Secrets Never Committed | DB credentials and JWT signing key read via `pydantic-settings` from environment variables populated by `.env` (gitignored); `.env.example` committed instead | PASS |

No violations requiring justification. Complexity Tracking table is not
needed.

**Post-design re-check** (after Phase 1 data-model/contracts/quickstart):
the effective-dated `budgets` table, cookie-carried JWT, and migration-seeded
`categories` table (see [research.md](./research.md) and
[data-model.md](./data-model.md)) introduce no sync DB access, no
non-migration schema path, and no host-only dependency. All six gates still
PASS; no new Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/001-expense-tracker-mvp/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md         # Phase 1 output (/speckit-plan command)
├── contracts/            # Phase 1 output (/speckit-plan command)
│   └── web-routes.md
└── tasks.md               # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
app/
├── main.py                 # FastAPI app factory, router registration, startup
├── config.py                # pydantic-settings: DB URL, JWT secret, env-driven
├── db/
│   ├── session.py            # async engine + AsyncSession factory
│   └── base.py                 # declarative Base
├── models/
│   ├── user.py
│   ├── category.py
│   ├── expense.py
│   └── budget.py
├── schemas/
│   ├── auth.py
│   ├── expense.py
│   └── budget.py
├── security/
│   ├── passwords.py           # bcrypt hash/verify
│   └── jwt.py                    # token creation/verification, cookie extraction
├── dependencies.py           # get_db, get_current_user
├── routers/
│   ├── auth.py                  # register, login, logout pages + form handlers
│   ├── expenses.py             # add + list expense pages + form handlers
│   ├── summary.py               # monthly totals-by-category page
│   └── budgets.py               # set budget + budget-vs-actual page
├── templates/
│   ├── base.html
│   ├── register.html
│   ├── login.html
│   ├── expenses_list.html
│   ├── expense_form.html
│   ├── summary.html
│   └── budget.html
└── static/
    └── styles.css

alembic/
├── env.py
└── versions/
    └── 0001_initial_schema.py   # creates users, categories, expenses,
                                  # budgets tables + seeds the 7 fixed
                                  # categories

tests/
├── conftest.py               # async engine/session fixtures, AsyncClient
│                              # fixture against the real Postgres service
├── test_auth.py
├── test_expenses.py
├── test_summary.py
└── test_budgets.py

docker-compose.yml             # app + db (postgres:16) services
Dockerfile
alembic.ini
pyproject.toml                 # or requirements.txt
.env.example
```

**Structure Decision**: Single backend service (Option 1 style, adapted for
a server-rendered web app: no separate `frontend/` project because Jinja2
templates and static CSS are served directly by the FastAPI app under
`app/templates` and `app/static`). This matches the constitution's
single-stack, Docker-Compose-first model and avoids an unnecessary
frontend/backend split for a feature with no client-side app.

## Complexity Tracking

*No Constitution Check violations — this section is not needed.*
