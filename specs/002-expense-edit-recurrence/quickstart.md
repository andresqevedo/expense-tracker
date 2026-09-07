# Quickstart: Retroactive Expense Editing and Recurring Transactions

Validates this feature end-to-end against [spec.md](./spec.md) Success
Criteria. See [data-model.md](./data-model.md) and
[contracts/web-routes.md](./contracts/web-routes.md) for field-level and
route-level detail. Builds on spec 001's
[quickstart.md](../001-expense-tracker-mvp/quickstart.md); run that stack the
same way.

## Prerequisites

Same as spec 001: Docker + Docker Compose, and a `.env` file. No new
prerequisite is introduced by this feature.

## Run the stack

```bash
docker compose up --build
```

The new `recurring_expense_templates` and `recurring_occurrence_actions`
tables are created by this feature's Alembic migration, applied
automatically by the same `alembic upgrade head` entrypoint step spec 001
already runs on boot.

## Validation scenarios

1. **Backdate an expense within the current month** (US1, SC-002)
   - From `/expenses/new`, submit an expense dated a few days before today
     (still within the current calendar month).
   - Expect: saved, visible in `/expenses` and that month's `/summary`
     total.
   - Retry with a date in the previous calendar month: expect rejection
     stating dates before the current month aren't accepted.

2. **Record a refund** (US2, SC-001)
   - Submit a new expense with a negative amount (e.g. `-15.00`) and no
     description.
   - Expect: saved with description exactly `refund`.
   - Repeat with a description like `"store credit"`: expect `refund`
     appended, e.g. `"store credit refund"`.
   - Repeat with a description that already says `"Refunded by store"`:
     expect it saved unchanged (no double-tagging).
   - Check `/summary` and `/budgets` for that category: expect the negative
     amount netted against the category's other expenses.

3. **Edit a current-month expense** (US3, SC-003)
   - Edit an expense recorded earlier in the current month: change its
     amount, category, or date (still within the current month).
   - Expect: saved, `/summary` and `/budgets` reflect the new value.
   - Attempt to edit an expense from a prior month (if any exist from
     before this feature shipped, or simulate via direct DB insert):
     expect the edit rejected and the expense unchanged.

4. **Privacy check** (SC-004)
   - As a second, separately-registered user, confirm neither `/expenses`
     edit routes nor `/recurring` ever expose or accept the first user's
     expense or template identifiers.

5. **Set up and confirm a recurring expense** (US4, SC-005, SC-006)
   - On `/recurring`, create a template (e.g. monthly, category "Housing",
     amount `1200.00`).
   - Expect: template listed as active; if its anchor due date has already
     passed this month, a pending occurrence appears immediately.
   - Confirm the pending occurrence as-is: expect an expense created dated
     on the occurrence's due date, visible in `/expenses` and counted in
     `/summary`/`/budgets` identically to a manually entered expense.
   - Create a second template and skip its first pending occurrence:
     expect no expense created, and the occurrence never reappears.
   - Create a third template and use "adjust and add" to change its amount
     before adding: expect the resulting expense to use the adjusted
     amount, not the template's original one.

6. **Manage a recurring template** (US5)
   - Edit an active template's amount: expect a not-yet-actioned pending
     occurrence (if any remain this month) to reflect the new amount, while
     any expense already confirmed earlier keeps its original amount.
   - Cancel the template: expect its remaining pending occurrences to
     disappear from `/recurring`, and no new ones to ever appear again,
     while previously confirmed expenses remain in `/expenses`.

## Automated tests

```bash
docker compose --profile test run --rm --build test pytest
```

Per Constitution Principle II, these run against the real PostgreSQL
service via the dedicated `test` Compose profile, not SQLite or a mocked DB
layer (see `CLAUDE.md` § Docker Test Workflow). Includes latency-budget
assertions (SC-007) for this feature's new routes, following spec 001's
`time.perf_counter()` pattern.
