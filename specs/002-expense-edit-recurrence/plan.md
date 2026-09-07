# Implementation Plan: Retroactive Expense Editing and Recurring Transactions

**Branch**: `002-expense-edit-recurrence` | **Date**: 2026-09-07 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-expense-edit-recurrence/spec.md`

## Summary

Extends the existing expense tracker with three capabilities, all scoped to
the current calendar month to protect closed months' totals: (1) recording a
new expense dated earlier in the current month, not just today; (2) editing
an existing current-month expense's amount, category, date, or description,
including recording a refund as a new negative-amount expense with "refund"
auto-tagged in its description; and (3) recurring expense templates that,
rather than auto-generating expenses in the background, surface a pending
occurrence each time the user visits in a new calendar month for the user to
confirm as-is, adjust and add, or skip. No new infrastructure, background
job scheduler, or dependency is required: recurring occurrences are computed
statelessly, on request, from each active template plus a small table
tracking which occurrences have already been confirmed or skipped.

## Technical Context

**Language/Version**: Python 3.12 (unchanged)

**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 (async), Alembic, Jinja2,
Pydantic v2 (unchanged from spec 001; no new dependency is required, since
recurring occurrences are computed on request rather than by a background
scheduler)

**Storage**: PostgreSQL 16, run via Docker Compose (unchanged). Two new
tables: `recurring_expense_templates` and `recurring_occurrence_actions`
(see [data-model.md](./data-model.md)).

**Testing**: pytest, pytest-asyncio, httpx.AsyncClient (ASGITransport)
against the real PostgreSQL instance (Constitution Principle II), extending
the existing `tests/` suite and `conftest.py` fixtures unchanged.

**Target Platform**: Linux server container (Docker Compose), accessed via
browser (unchanged)

**Project Type**: Web application, server-rendered single backend service
(unchanged; no separate frontend project)

**Performance Goals**: Per spec Clarifications and SC-007, this feature's new
routes (expense edit, recurring template create/cancel, occurrence
confirm/adjust/skip) inherit spec 001's 200ms per-request server-side
latency budget, verified the same way (automated `time.perf_counter()`
assertions in the test suite, per spec 001's precedent).

**Constraints**: Must run entirely via `docker compose up --build` with no
host dependency beyond Docker (Constitution Principle V); all DB access
async (Principle IV); all schema changes via Alembic (Principle III);
secrets only via environment variables (Principle VI). No background job
runner is introduced (see [research.md](./research.md) § Occurrence
generation strategy).

**Scale/Scope**: Same MVP-scale, single-user-per-account assumption as spec
001; a user's recurring templates and pending-occurrence computation are
expected to stay in the low tens per user, not requiring pagination.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Result |
|---|---|---|
| I. Test-First Development | Each new/changed route (expense edit, refund via existing create route, recurring template create/cancel, occurrence confirm/adjust/skip) gets a failing test committed before its implementation; tasks.md will sequence tests before implementation per route | PASS |
| II. Real Database, No Shortcuts | New tests extend the existing `tests/` suite, running via `httpx.AsyncClient` against the app wired to the real PostgreSQL 16 service through the dedicated `test` Compose service/profile; no SQLite/mock substitution | PASS |
| III. Migrations Are the Only Schema Change Path | `recurring_expense_templates` and `recurring_occurrence_actions` are created via a new Alembic migration; `Base.metadata.create_all` is not used | PASS |
| IV. Async All the Way Down | All new route handlers, occurrence-computation helpers, and queries use `async def` and `AsyncSession`, consistent with the existing codebase | PASS |
| V. Docker Is the Source of Truth | No new dependency, so no change to `pyproject.toml`/`uv.lock`/the multi-stage Dockerfile is required; the existing lean, non-root `final` image and gated `test` service are unaffected | PASS |
| VI. Secrets Never Committed | This feature introduces no new secret or credential | PASS |

No violations requiring justification. Complexity Tracking table is not
needed.

**Post-design re-check** (after Phase 1 data-model/contracts/quickstart):
the two new tables, the (template_id, due_date) composite identity for an
occurrence action, and the reuse of `expenses.amount` (already `Numeric(10,2)`,
already nullable-description) for negative refund amounts introduce no sync
DB access, no non-migration schema path, no new host dependency, and no new
secret. All six gates still PASS; no new Complexity Tracking entries
required.

## Project Structure

### Documentation (this feature)

```text
specs/002-expense-edit-recurrence/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md         # Phase 1 output (/speckit-plan command)
├── quickstart.md          # Phase 1 output (/speckit-plan command)
├── contracts/               # Phase 1 output (/speckit-plan command)
│   └── web-routes.md
└── tasks.md                    # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
app/
├── models/
│   ├── expense.py                     # unchanged (amount already Numeric(10,2), already signed-capable)
│   ├── recurring_template.py           # NEW: RecurringExpenseTemplate
│   └── recurring_occurrence.py          # NEW: RecurringOccurrenceAction
├── schemas/
│   ├── expense.py                     # CHANGED: amount validator allows negative; refund-description rule; date validator uses current-month window instead of today-only
│   └── recurring.py                    # NEW: RecurringTemplateForm, OccurrenceAdjustForm
├── routers/
│   ├── expenses.py                    # CHANGED: add GET/POST /expenses/{expense_id}/edit
│   └── recurring.py                     # NEW: GET/POST /recurring, POST /recurring/{template_id}/cancel,
│                                        #      POST /recurring/{template_id}/occurrences/{due_date}/confirm,
│                                        #      GET/POST /recurring/{template_id}/occurrences/{due_date}/adjust,
│                                        #      POST /recurring/{template_id}/occurrences/{due_date}/skip
├── templates/
│   ├── expense_form.html              # CHANGED: reused for both add and edit (parameterized action URL, pre-filled values)
│   ├── recurring_list.html             # NEW: active templates + this month's pending occurrences
│   └── recurring_occurrence_adjust.html # NEW: adjust-one-occurrence form
└── main.py                             # CHANGED: register the new recurring router

alembic/versions/
└── 0002_recurring_expenses.py          # NEW: creates recurring_expense_templates, recurring_occurrence_actions

tests/
├── test_expenses.py                   # CHANGED: add edit, refund, backdate, and latency-budget tests
└── test_recurring.py                    # NEW: template create/cancel, occurrence confirm/adjust/skip, isolation, latency
```

**Structure Decision**: Extends the existing single backend service from
spec 001 (no new project or service). Editing reuses the existing
`expense_form.html` template and `POST /expenses` route's validation schema
(`ExpenseForm`) rather than introducing parallel create/edit code paths, per
[research.md](./research.md). Recurring templates and occurrences get their
own router, models, and schema module since they introduce a genuinely new
domain concept, but follow the same conventions (Pydantic form schema +
`field_errors` re-render pattern, `Depends(get_current_user)`/`Depends(get_db)`)
already established by `app/routers/budgets.py` and `app/routers/expenses.py`.

## Complexity Tracking

*No Constitution Check violations. This section is not needed.*
