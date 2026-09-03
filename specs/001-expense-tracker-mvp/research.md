# Phase 0 Research: Expense Tracker MVP

All primary technology choices (FastAPI, Python 3.12, SQLAlchemy 2.0 async,
Alembic, PostgreSQL 16, Docker Compose, JWT, Jinja2 + plain CSS, pytest +
httpx.AsyncClient) were specified directly by the user and are fixed by the
project constitution. The items below resolve the remaining implementation
decisions needed before design.

## 1. Carrying a JWT through a server-rendered (non-JS) app

**Decision**: Issue the JWT at login/register and store it in an
`HttpOnly`, `Secure`, `SameSite=Lax` cookie (`access_token`). A FastAPI
dependency reads the JWT from that cookie (falling back to an
`Authorization: Bearer` header, to keep the mechanism usable by non-browser
clients/tests) and resolves the current user. The token is signed with
HS256 using the constitution's single JWT signing-key secret, and expires
24 hours after issuance (per Clarifications, Session 2026-09-03); there is
no refresh-token mechanism in this MVP, so an expired token requires a
fresh login.

**Rationale**: The spec's UI is server-rendered HTML with plain CSS — no
JavaScript layer to attach an `Authorization` header to on every request.
An `HttpOnly` cookie lets the browser send the token automatically like a
session cookie while the token itself remains a standard signed JWT
(satisfying the constitution's "JWT bearer tokens" / "JWT signing key"
requirement) rather than a server-side session store.

**Alternatives considered**:
- Plain server-side session (opaque cookie + session table) — rejected,
  contradicts the explicit instruction to use JWT bearer tokens.
- Requiring an `Authorization` header from a JS fetch layer — rejected, no
  JS framework is in scope; forms are plain HTML.

## 2. Password hashing

**Decision**: `passlib[bcrypt]` (bcrypt hashing with a per-password salt).

**Rationale**: Industry-standard, well-supported in the FastAPI/Python
ecosystem, and satisfies FR-001a's minimum password policy without adding
a dependency the constitution doesn't already imply.

**Alternatives considered**: `argon2` (also fine, slightly heavier
dependency footprint for an MVP) — deferred, bcrypt is sufficient and more
common in existing FastAPI tutorials/tooling.

## 3. Modeling the per-month budget history

**Decision**: A `budgets` table keyed by `(user_id, category_id,
effective_month)` where `effective_month` is the first day of the month
the budget amount became active. Setting/updating a budget writes a row for
the current month (upserting if one already exists for that month). To
resolve the budget in effect for a target month, the query selects the row
with the latest `effective_month <= target_month` for that user+category;
no row found means "no budget set" for that month (FR-015).

**Rationale**: Directly implements the clarified semantics — updating a
budget affects the current and future months while past months keep the
value that was active for them — as a simple forward-fill over an
effective-dated table, with no need to write a row per future month.

**Alternatives considered**:
- Single mutable `budgets.amount` field per category (no history) —
  rejected, contradicts the clarification (past months must retain their
  historical value).
- A row per (user, category, month) requiring explicit rows for every
  future month — rejected, unnecessary write amplification; forward-fill
  achieves the same semantics from a single row per change.

## 4. Categories as a seeded lookup table vs. an enum

**Decision**: A `categories` table with a unique `name` column, seeded with
the 7 fixed values (Food, Transportation, Housing, Utilities,
Entertainment, Health, Other) via the initial Alembic migration's data
insert. `expenses.category_id` and `budgets.category_id` are foreign keys
into it.

**Rationale**: Keeps category data itself under migration control
(Constitution Principle III) rather than hardcoding it as a Python
`Enum` that would require a code deploy (and a separate DB constraint) to
ever change, and makes referential integrity (an expense/budget always
points at a real category) enforced by the database.

**Alternatives considered**: Python `Enum` + DB `CHECK` constraint —
rejected, splits the source of truth between code and schema for data that
is naturally a migration-seeded table.

## 5. Testing against real PostgreSQL (Constitution Principle II)

**Decision**: `tests/conftest.py` provisions an async engine/session
against the same PostgreSQL 16 service defined in `docker-compose.yml`
(a dedicated test database on that instance), runs Alembic migrations (or
equivalent schema setup) once per test session, and wraps each test in a
transaction that's rolled back afterward for isolation. `httpx.AsyncClient`
with `ASGITransport` drives the FastAPI app in-process against that DB.

**Rationale**: Satisfies the constitution's ban on SQLite/in-memory/mocked
DB substitution while keeping tests fast (transaction rollback instead of
recreating the schema per test) and reproducible via `docker compose up`.

**Alternatives considered**: `pytest-postgresql` spinning up an ephemeral
Postgres — rejected, adds a host dependency outside Docker Compose,
conflicting with Principle V.
