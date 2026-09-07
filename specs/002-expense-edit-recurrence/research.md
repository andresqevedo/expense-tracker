# Research: Retroactive Expense Editing and Recurring Transactions

## Occurrence generation strategy

**Decision**: Recurring occurrences are computed on request, not pre-generated
or produced by a background job. Only a *decision* (confirmed or skipped) on
a given (template, due date) pair is persisted, in
`recurring_occurrence_actions`. A "pending" occurrence has no row at all: it
is simply a due date, produced by an active template's frequency within the
current calendar month, for which no action row yet exists.

**Rationale**: Spec Clarifications (Session 2026-09-07) resolved occurrence
generation to Option C (user-confirmed) with a stateless, current-month-only
computation and no backfill. Persisting only actioned occurrences is the
direct, minimal implementation of that rule: there is nothing to backfill or
clean up, and "current month's pending occurrences" is always exactly
"due dates this template's frequency produces this month, minus due dates
already actioned this month," computed fresh on every request.

**Alternatives considered**:
- A background scheduler (APScheduler/Celery) generating expenses or
  pending-occurrence rows on a cron: rejected. It contradicts the spec's
  explicit "no background generation" decision, and this codebase has no
  existing job-runner infrastructure to introduce for a single feature.
- Pre-generating all future occurrence rows at template-creation time:
  rejected. It requires unbounded row growth and a cleanup/backfill story
  the spec explicitly ruled out (stateless, current-month-only).

## Occurrence due-date anchor

**Decision**: A template's occurrence due dates are anchored to its creation
date: a weekly template repeats every 7 days from its creation date's
weekday; a monthly template repeats on its creation date's day-of-month
(falling back to the month's last valid day when that day doesn't exist,
per FR-018); a yearly template repeats on its creation date's month and day.

**Rationale**: The spec deliberately keeps "frequency" abstract (FR-010) and
never introduces a separate start-date field, since User Story 4's
acceptance scenarios only ask for "an amount, category, description, and
frequency." Using the creation date as the anchor is the simplest
interpretation consistent with that scope, and needs no extra required
field or user decision at creation time.

**Alternatives considered**:
- A separate, user-chosen start date field: rejected as scope the spec never
  asked for; every acceptance scenario for User Story 4 omits it.

## Refund detection and description tagging

**Decision**: Implemented as a Pydantic `model_validator(mode="after")` on
`ExpenseForm`, checking `amount < 0` and appending `"refund"` to
`description` (case-insensitive containment check) when absent. This applies
identically whether the form is used to create or edit an expense, and to
the adjust-and-add path on a pending occurrence, since all three funnel
through the same schema (per FR-004, FR-007, FR-012).

**Rationale**: Keeps the refund rule colocated with the other field-level
rules already expressed as validators on `ExpenseForm` (amount truncation,
category, date), rather than duplicating the check across three route
handlers.

**Alternatives considered**:
- Applying the rule in each route handler after schema validation: rejected
  as it scatters one business rule across three call sites, risking drift.

## Current-month window enforcement

**Decision**: Reuses the existing `_month_start`/`_next_month_start` helpers
(currently private to `app/routers/summary.py` and already imported by
`app/routers/budgets.py`) as the single source of truth for "the current
calendar month," per FR-001's definition (the server's UTC calendar day at
request time). `ExpenseForm`'s date validator is changed from "must equal
today" to "must fall within `[_month_start(None), today]`," and the edit
route additionally checks the *existing* expense's stored date against the
same window before allowing an edit (FR-005, FR-006).

**Rationale**: Both helpers are already tested indirectly via
`test_summary.py` and `test_budgets.py`; reusing them avoids a second,
potentially inconsistent definition of "current month" and directly
satisfies FR-001's requirement that every reference to "the current
calendar month" in this feature use the same definition.

**Alternatives considered**:
- Duplicating month-boundary logic inside `ExpenseForm`: rejected as an
  unnecessary second implementation of the same rule.

## Edit route shape

**Decision**: `GET /expenses/{expense_id}/edit` (render, pre-filled) and
`POST /expenses/{expense_id}/edit` (submit), reusing `expense_form.html` and
`ExpenseForm`, mirroring the existing `GET`/`POST /expenses/new` pair.

**Rationale**: Matches the established router convention in this codebase
(`app/routers/expenses.py`, `app/routers/budgets.py`) rather than
introducing a different pattern (e.g., a JSON PATCH endpoint) that the rest
of this server-rendered app doesn't use.

**Alternatives considered**:
- A single unified `POST /expenses` handling both create and update via a
  hidden form field: rejected as it would complicate `ExpenseForm` and the
  route's control flow for no real benefit over two small, explicit routes.

## Latency budget tests for new routes

**Decision**: New routes get the same `time.perf_counter()`-based assertion
pattern already used in `tests/test_auth.py::test_register_latency_budget`
and `tests/test_expenses.py::test_add_expense_latency_budget`, asserting
each stays under 200ms per SC-007.

**Rationale**: Direct reuse of an already-working, already-reviewed pattern
from spec 001; no new tooling or dependency required.

**Alternatives considered**: None seriously considered; spec 001 already
settled the "how" for this exact kind of assertion.
