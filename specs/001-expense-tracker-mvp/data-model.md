# Phase 1 Data Model: Expense Tracker MVP

Source: [spec.md](./spec.md) Key Entities section, Functional Requirements,
and Clarifications. All tables live in PostgreSQL 16 and are created only
via Alembic migrations (Constitution Principle III).

## User

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK, server-generated (satisfies spec's "unique identifier that is not the email itself") |
| `email` | citext / text | unique, not null, indexed |
| `password_hash` | text | not null (bcrypt hash; never store plaintext) |
| `created_at` | timestamptz | not null, default now() |

**Validation rules** (FR-001, FR-001a, FR-002):
- Email must be a syntactically valid email address.
- Password must be ≥ 8 characters and contain at least one letter and at
  least one digit before hashing.
- `email` uniqueness enforced by a DB unique constraint (source of truth)
  and checked pre-insert for a friendly error message.

**Relationships**: one User → many Expense; one User → many Budget rows.

## Category

| Field | Type | Constraints |
|---|---|---|
| `id` | smallint / int | PK |
| `name` | text | unique, not null |

**Fixed data** (seeded by the initial migration, per Clarifications):
Food, Transportation, Housing, Utilities, Entertainment, Health, Other.
Not user-owned, not user-editable in this MVP; no create/update/delete
route exists for categories.

**Relationships**: one Category → many Expense; one Category → many
Budget rows.

## Expense

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK, server-generated |
| `user_id` | UUID | FK → users.id, not null, indexed |
| `category_id` | int | FK → categories.id, not null |
| `amount` | numeric(10,2) | not null, > 0 |
| `date` | date | not null |
| `description` | text | nullable |
| `created_at` | timestamptz | not null, default now() |

**Validation rules** (FR-006, FR-007, FR-007a):
- `amount` must be strictly positive; it is stored with exactly 2 decimal
  places. A value submitted with more precision is rounded down
  (truncated, not standard rounding) to 2 decimal places rather than
  rejected — e.g. `12.345` is truncated to `12.34` (not rounded up to
  `12.35`); `12.3` is accepted and stored/displayed as `12.30`.
- `category_id` must reference an existing category (selection is
  required — no default/blank category).
- `date` must equal the current server date at submission time (UTC
  calendar day); any other date, or a non-date value, is rejected.
- `description` is optional free text with no additional MVP-level
  validation.

**Relationships**: belongs to exactly one User (FR-008) and exactly one
Category. Listing (FR-009) orders by `date` descending, then `created_at`
descending as a tiebreaker for same-day entries.

## Budget

Modeled as an **effective-dated** row per change, per the Clarifications
("Per-month budget history"):

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | PK, server-generated |
| `user_id` | UUID | FK → users.id, not null |
| `category_id` | int | FK → categories.id, not null |
| `effective_month` | date | not null; always the 1st of a month |
| `amount` | numeric(10,2) | not null, > 0 |
| `created_at` | timestamptz | not null, default now() |

**Validation rules**: `amount` must be strictly positive; a value
submitted with more than 2 decimal places is rounded down (truncated) to
2 decimal places rather than rejected, matching the Expense amount rule
(FR-007a).

**Constraints**: unique on `(user_id, category_id, effective_month)` — at
most one budget value can be "set" for a given category in a given month;
setting a budget again for the same category within the same month
**updates** that row (does not create a second history entry for the same
month).

**Resolution rule** (used by the budget-vs-actual view, FR-014, FR-015):
for a target `(user, category, month)`, select the row with the greatest
`effective_month <= target month`. No such row ⇒ "no budget set" for that
category/month (distinct from a budget of 0, per FR-015). This also
implements FR-013: creating a new row for the current month leaves all
prior rows (and therefore all past months' resolved budgets) untouched.

**Relationships**: belongs to exactly one User and exactly one Category.

## Derived view: Monthly total by category (FR-011)

Not a stored entity — computed as `SUM(expenses.amount)` grouped by
`expenses.category_id`, filtered to `expenses.user_id = :user` and
`expenses.date` within the selected month, joined to `categories.name`
for display. A category with no expenses that month is omitted from
non-empty months and the whole set is empty for a month with none (US4
scenario 3).

## Derived view: Budget vs. Actual (FR-014, FR-015)

Not a stored entity — for each category with either a resolved budget
(per the Budget resolution rule above) or actual expenses in the selected
month, computed as:

- `budgeted_amount` = resolved budget amount, or `null` if none set
- `actual_amount` = monthly total for that category (0 if none)
- `difference` = `budgeted_amount - actual_amount` when a budget exists;
  undefined/not shown when `budgeted_amount` is `null`
- `status` = `no_budget` | `under` | `on_budget` (difference = 0.00) |
  `over`, derived from the two amounts above at 2-decimal precision
