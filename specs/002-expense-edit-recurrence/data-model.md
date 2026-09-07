# Data Model: Retroactive Expense Editing and Recurring Transactions

## Expense (extended, no schema migration)

Unchanged table shape (`app/models/expense.py`); only application-level
validation rules change.

| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | unchanged |
| user_id | UUID, FK → users.id | unchanged |
| category_id | int, FK → categories.id | unchanged |
| amount | Numeric(10,2) | **Rule changed**: non-zero required (was: strictly positive). Negative values represent a refund/credit (FR-003). Already nullable-free; column type needs no migration since `Numeric` already stores negative values. |
| date | Date | **Rule changed**: must fall within `[current calendar month's first day, today]` (was: must equal today). Applies to both new and edited expenses (FR-001, FR-005). |
| description | String, nullable | **Rule added**: when `amount < 0`, MUST contain "refund" (case-insensitive); appended automatically if absent (FR-004). |
| created_at | DateTime | unchanged |

**Edit eligibility rule** (FR-005, FR-006): an expense may be edited only
while its *currently stored* `date` falls within the current calendar month.
Enforced in the edit route, not the schema (the schema validates the
*submitted* date; the route additionally checks the *existing row's* date
before allowing any edit at all).

## RecurringExpenseTemplate (new table: `recurring_expense_templates`)

| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | `default=uuid.uuid4`, matching existing model conventions |
| user_id | UUID, FK → users.id, indexed | ownership/isolation (FR-016) |
| category_id | int, FK → categories.id | from the same fixed set as expenses |
| amount | Numeric(10,2) | MUST be positive; zero/negative rejected (FR-010a) |
| description | String, nullable | optional, per FR-010 |
| frequency | String | one of `weekly`, `monthly`, `yearly`; validated at the Pydantic layer (`Literal`), not DB-enforced, consistent with this codebase's existing preference for lightweight string fields over a dedicated lookup table for small fixed sets used only within one entity. **Immutable after creation** (FR-014a). |
| status | String | one of `active`, `canceled`. Set to `canceled` by FR-015; no reactivation (see spec Assumptions). |
| created_at | DateTime(timezone=True) | server default `now()`; also serves as the occurrence due-date anchor (see research.md § Occurrence due-date anchor) |

No `updated_at`/history table: editing a template's amount/category/
description (FR-014) overwrites the row in place, consistent with this
project's existing no-edit-history scope decision (spec 001 and spec 002
Assumptions).

## RecurringOccurrenceAction (new table: `recurring_occurrence_actions`)

Represents a *decision* made on one (template, due date) pair. A due date
with no row here is, by definition, still pending (see research.md §
Occurrence generation strategy); this table never stores "pending" rows.

| Field | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| template_id | UUID, FK → recurring_expense_templates.id, indexed | |
| due_date | Date | the specific occurrence date this action resolves |
| status | String | one of `confirmed`, `skipped` |
| expense_id | UUID, FK → expenses.id, nullable | set when `status = confirmed` (covers both the as-is confirm and the adjust-and-add path, FR-012); `NULL` when `status = skipped` |
| created_at | DateTime(timezone=True) | server default `now()` |

**Unique constraint**: `(template_id, due_date)`. An occurrence can be
actioned at most once (FR-013); a second attempt to confirm/skip an
already-actioned due date is rejected at the database level as a defense in
depth behind the application-level pending-list computation.

## Pending occurrence computation (derived, not stored)

For a given user and the current calendar month `[month_start, today]`
(per FR-001's definition):

1. For each of the user's `active` `RecurringExpenseTemplate` rows, compute
   the set of due dates its frequency produces within `[month_start, today]`,
   anchored to the template's `created_at` date (research.md), resolving a
   nonexistent day-of-month to that month's last valid day (FR-018).
2. Exclude any due date that already has a matching
   `RecurringOccurrenceAction` row for that `template_id`.
3. The remaining (template, due_date) pairs are this request's pending
   occurrences (FR-011).

This is a read-time computation, not a persisted list, consistent with the
spec's "stateless, current month only, no backfill" resolution.

## Relationships

```text
User 1──* Expense
User 1──* RecurringExpenseTemplate
Category 1──* Expense
Category 1──* RecurringExpenseTemplate
RecurringExpenseTemplate 1──* RecurringOccurrenceAction
RecurringOccurrenceAction 0..1──0..1 Expense   (set only when confirmed)
```
