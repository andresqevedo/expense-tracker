---

description: "Task list for Retroactive Expense Editing and Recurring Transactions"
---

# Tasks: Retroactive Expense Editing and Recurring Transactions

**Input**: Design documents from `/specs/002-expense-edit-recurrence/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/web-routes.md](./contracts/web-routes.md), [quickstart.md](./quickstart.md)

**Tests**: Included. Constitution Principle I (Test-First Development) mandates a failing test committed before each route's implementation, same as spec 001; this is not optional for this project.

**Organization**: Tasks are grouped by user story (from spec.md, in priority order P1 → P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files or independent functions, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- File paths follow the structure in [plan.md](./plan.md) § Project Structure

## Path Conventions

Extends the existing single backend project from spec 001: `app/` (application
code), `alembic/` (migrations), `tests/` at repository root. No new project or
service is introduced.

---

## Phase 1: Setup

**Purpose**: Confirm no new project-level setup is required

- [ ] T001 Confirm no new dependency is required (per plan.md and research.md): `pyproject.toml`/`uv.lock` and the multi-stage `Dockerfile` remain unchanged for this feature

**Checkpoint**: No setup work blocks Foundational or story work; proceed directly.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema and shared validation changes that multiple user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Create `RecurringExpenseTemplate` model in `app/models/recurring_template.py` per data-model.md § RecurringExpenseTemplate (UUID PK, user_id FK, category_id FK, amount numeric(10,2), description nullable, frequency string, status string, created_at)
- [ ] T003 [P] Create `RecurringOccurrenceAction` model in `app/models/recurring_occurrence.py` per data-model.md § RecurringOccurrenceAction (UUID PK, template_id FK, due_date, status string, expense_id nullable FK, created_at; unique on template_id+due_date)
- [ ] T004 Generate and write the Alembic migration `alembic/versions/0002_recurring_expenses.py` creating the `recurring_expense_templates` and `recurring_occurrence_actions` tables (depends on: T002, T003)
- [ ] T005 Update `app/schemas/expense.py`'s `ExpenseForm`: change the amount validator to reject only exactly zero (negative now valid, representing a refund, FR-003); change the date validator to accept any date in `[current calendar month's first day, today]` instead of only today (FR-001, FR-002, reusing `_month_start`/`_next_month_start` from `app/routers/summary.py` per research.md); add a `model_validator(mode="after")` that appends "refund" (case-insensitive check) to `description` when `amount < 0` and it's absent (FR-004)

**Checkpoint**: `alembic upgrade head` succeeds; `ExpenseForm` enforces the new rules. User Story 1, 2, and 3 implementation can now begin (they all build on T005); User Story 4 and 5 additionally need T002–T004.

---

## Phase 3: User Story 1 - Add an Expense for a Past Date (Priority: P1) 🎯 MVP

**Goal**: A logged-in user can record an expense dated earlier in the current calendar month, not only today.

**Independent Test**: Submit a new expense dated a few days before today (same month); confirm it's saved and counted in that month's totals. Submit one dated in the previous month; confirm it's rejected.

### Tests for User Story 1

> Write these tests FIRST; confirm they FAIL before implementation (Constitution Principle I)

- [ ] T006 [P] [US1] Test `POST /expenses` accepts a date earlier in the current calendar month and saves it, in `tests/test_expenses.py::test_add_expense_backdated_within_month`
- [ ] T007 [P] [US1] Test `POST /expenses` rejects a date in the previous calendar month, in `tests/test_expenses.py::test_add_expense_rejects_prior_month`
- [ ] T008 [P] [US1] Update the existing `test_add_expense_invalid_date` in `tests/test_expenses.py`: replace its "yesterday" rejected-date case with a genuine previous-calendar-month date, since backdating within the current month is now allowed; keep the future-date and invalid-string cases unchanged

### Implementation for User Story 1

- [ ] T009 [US1] Update `app/templates/expense_form.html`: change the date input from `readonly`-fixed-to-today to an editable date picker with `min` set to the current month's first day and `max` set to today (server-side validation via T005 remains the source of truth) (depends on: T005)

**Checkpoint**: User Story 1 is independently functional and testable.

---

## Phase 4: User Story 2 - Record a Refund (Priority: P1)

**Goal**: A logged-in user can record a refund as a new expense with a negative amount, auto-tagged with "refund" in its description, netted against category totals.

**Independent Test**: Submit a new expense with a negative amount and no description; confirm it saves with description "refund" and reduces that category's monthly total.

### Tests for User Story 2

> Write these tests FIRST; confirm they FAIL before implementation

- [ ] T010 [P] [US2] Test `POST /expenses` with a negative amount and no description saves with description exactly "refund", in `tests/test_expenses.py::test_add_expense_refund_default_description`
- [ ] T011 [P] [US2] Test `POST /expenses` with a negative amount and a description not containing "refund" appends it, in `tests/test_expenses.py::test_add_expense_refund_appends_description`
- [ ] T012 [P] [US2] Test `POST /expenses` with a negative amount and a description already containing "refund" (any letter case) saves unchanged, in `tests/test_expenses.py::test_add_expense_refund_no_double_tag`
- [ ] T013 [P] [US2] Test `POST /expenses` rejects an amount of exactly zero, in `tests/test_expenses.py::test_add_expense_zero_amount_rejected`
- [ ] T014 [P] [US2] Update the existing `test_add_expense_invalid_amount` in `tests/test_expenses.py`: remove the negative-amount case from the rejected list (negative is now valid), keep zero and empty-string rejected
- [ ] T015 [P] [US2] Test a negative (refund) expense nets against its category's monthly total, in `tests/test_summary.py::test_summary_nets_refund`
- [ ] T016 [P] [US2] Test a negative (refund) expense nets against actual spend in the budget comparison, in `tests/test_budgets.py::test_budget_actual_nets_refund`

### Implementation for User Story 2

- [ ] T017 [US2] Update `app/templates/expense_form.html`: remove the `min="0.01"` constraint on the amount input (client-side hint only; negative values must be enterable), keep `step="any"` (depends on: T005)

**Checkpoint**: User Stories 1 AND 2 both work independently.

---

## Phase 5: User Story 3 - Edit a Previously Recorded Expense (Priority: P1)

**Goal**: A logged-in user can edit a current-month expense's amount, category, date, or description; a prior-month expense is read-only.

**Independent Test**: Edit an expense recorded earlier in the current month; confirm the change is saved and reflected in that month's totals and budget comparison.

### Tests for User Story 3

> Write these tests FIRST; confirm they FAIL before implementation

- [ ] T018 [P] [US3] Test `GET /expenses/{expense_id}/edit` renders a pre-filled form for the current user's own current-month expense, in `tests/test_expenses.py::test_edit_expense_form_prefilled`
- [ ] T019 [P] [US3] Test `POST /expenses/{expense_id}/edit` updates amount/category/date/description and the change is reflected in `/summary` and `/budgets`, in `tests/test_expenses.py::test_edit_expense_success`
- [ ] T020 [P] [US3] Test `GET` and `POST /expenses/{expense_id}/edit` reject an expense dated in a prior calendar month (not-found), in `tests/test_expenses.py::test_edit_expense_rejects_prior_month`
- [ ] T021 [P] [US3] Test `POST /expenses/{expense_id}/edit` rejects a zero amount, missing category, or a date outside the current month, and leaves the original expense unchanged, in `tests/test_expenses.py::test_edit_expense_invalid_input`
- [ ] T022 [P] [US3] Test `GET` and `POST /expenses/{expense_id}/edit` reject another user's expense (not-found), in `tests/test_expenses.py::test_edit_expense_isolation`

### Implementation for User Story 3

- [ ] T023 [US3] Implement `GET /expenses/{expense_id}/edit` and `POST /expenses/{expense_id}/edit` in `app/routers/expenses.py`: look up the expense scoped to `current_user.id`, respond not-found if missing or its stored date has left the current calendar month, otherwise reuse `ExpenseForm` and `_render_expense_form` (parameterized action URL) for validation and re-render (depends on: T005)
- [ ] T024 [P] [US3] Update `app/templates/expense_form.html` to support edit mode: parameterize the form's `action` URL and pre-fill non-today values using the same date-input rules as User Story 1 (depends on: T009)
- [ ] T025 [US3] Add an "Edit" link per row in `app/templates/expenses_list.html`, shown only for expenses dated within the current calendar month (depends on: T023)

**Checkpoint**: User Stories 1–3 all work independently; the core "retroactive editing" ask is complete.

---

## Phase 6: User Story 4 - Set Up a Recurring Expense (Priority: P2)

**Goal**: A logged-in user can create a recurring template and, each month, confirm/adjust/skip the pending occurrences it produces.

**Independent Test**: Create a recurring template; confirm a pending occurrence appears and, once confirmed, an expense is created identical to a manual one.

### Tests for User Story 4

> Write these tests FIRST; confirm they FAIL before implementation

- [ ] T026 [P] [US4] Test `POST /recurring` creates an active template with amount/category/description/frequency, in `tests/test_recurring.py::test_create_recurring_template`
- [ ] T027 [P] [US4] Test `POST /recurring` rejects a zero or negative amount, in `tests/test_recurring.py::test_create_recurring_template_rejects_non_positive_amount`
- [ ] T028 [P] [US4] Test `GET /recurring` surfaces a pending occurrence for each due date an active template's frequency produces within the current month, including a template created mid-month whose anchor due date already passed, in `tests/test_recurring.py::test_pending_occurrences_current_month`
- [ ] T029 [P] [US4] Test confirming a pending occurrence creates an expense with the template's values dated on the due date and removes it from the pending list, in `tests/test_recurring.py::test_confirm_occurrence`
- [ ] T030 [P] [US4] Test the adjust-and-add path creates an expense using the adjusted values instead of the template's, in `tests/test_recurring.py::test_adjust_and_add_occurrence`
- [ ] T031 [P] [US4] Test the adjust-and-add path rejects an adjustment with a date outside the current month, a future date, or a zero amount, and leaves the occurrence pending, in `tests/test_recurring.py::test_adjust_and_add_invalid_input`
- [ ] T032 [P] [US4] Test skipping a pending occurrence creates no expense and that occurrence is never offered again, in `tests/test_recurring.py::test_skip_occurrence`
- [ ] T033 [P] [US4] Test a confirmed/adjusted recurring expense is counted identically to a manual expense in `/summary` and `/budgets`, and appears in `/expenses` carrying a visual recurring-origin indicator that a manually entered expense does not have (FR-017, FR-017a), in `tests/test_recurring.py::test_recurring_expense_appears_like_manual`
- [ ] T034 [P] [US4] Test no expense exists for a pending occurrence until it is confirmed or adjusted-and-added (SC-006), in `tests/test_recurring.py::test_no_auto_generated_expense`
- [ ] T035 [P] [US4] Test a weekly template's multiple due dates within one month each appear as separate, independently confirmable/skippable occurrences, in `tests/test_recurring.py::test_weekly_multiple_occurrences_same_month`
- [ ] T036 [P] [US4] Test a monthly template's due date resolves to the month's last valid day when its anchor day-of-month doesn't exist that month, in `tests/test_recurring.py::test_occurrence_day_resolution`
- [ ] T037 [P] [US4] Test a user's recurring templates, occurrences, and generated expenses are never visible to another user, in `tests/test_recurring.py::test_recurring_isolation`
- [ ] T038 [P] [US4] Test `POST /recurring` and the confirm/adjust/skip routes each respond within the 200ms latency budget (SC-007), in `tests/test_recurring.py::test_recurring_routes_latency_budget`

### Implementation for User Story 4

- [ ] T039 [US4] Create `app/schemas/recurring.py`: `RecurringTemplateForm` (positive amount, category_id, optional description, `frequency: Literal["weekly", "monthly", "yearly"]`) and `OccurrenceAdjustForm` (amount/date/category/description, same validation rules as `ExpenseForm`) (depends on: T002, T003, T005)
- [ ] T040 [US4] Implement the pending-occurrence computation helper in `app/routers/recurring.py`: for each of the user's active templates, compute due dates within the current month anchored to `created_at` per frequency, with the first occurrence being the creation date itself (FR-011a) (resolving a nonexistent day to the month's last valid day, FR-018), excluding any due date with an existing `RecurringOccurrenceAction` row (depends on: T002, T003, T039; data-model.md § Pending occurrence computation)
- [ ] T040a [P] [US4] Implement a recurrence-pattern label helper (e.g. "recurs on the 15th of each month", "recurs weekly on Wednesdays", "recurs yearly on March 3") derived from a template's `created_at` and `frequency` (FR-010b) (depends on: T002)
- [ ] T041 [US4] Implement `GET /recurring` and `POST /recurring` in `app/routers/recurring.py`: list active templates (canceled ones excluded, FR-015b) with their recurrence-pattern label (via T040a) and this month's pending occurrences (via T040); create a new template (depends on: T039, T040, T040a)
- [ ] T042 [US4] Implement `POST /recurring/{template_id}/occurrences/{due_date}/confirm` in `app/routers/recurring.py`: validate the due date is currently pending for that template, create the expense, record a `confirmed` action row (depends on: T040)
- [ ] T043 [US4] Implement `GET`/`POST /recurring/{template_id}/occurrences/{due_date}/adjust` in `app/routers/recurring.py`: render/validate adjusted values via `OccurrenceAdjustForm`; on success create the expense and a `confirmed` action row referencing it; on validation failure re-render with errors and leave the occurrence pending (depends on: T039, T040)
- [ ] T044 [US4] Implement `POST /recurring/{template_id}/occurrences/{due_date}/skip` in `app/routers/recurring.py`: validate the due date is currently pending, record a `skipped` action row (depends on: T040)
- [ ] T044a [US4] Update `GET /expenses` (`app/routers/expenses.py::list_expenses`) to also fetch, for each expense, whether a `RecurringOccurrenceAction` row references it (left outer join on `expense_id`), so the template can render a recurring-origin indicator (FR-017, FR-017a); no change to totals/aggregation queries (depends on: T003)
- [ ] T045 [P] [US4] Create `app/templates/recurring_list.html`: active templates with their recurrence-pattern label, create-template form, and this month's pending occurrences with confirm/adjust/skip actions (empty state if none)
- [ ] T045a [P] [US4] Update `app/templates/expenses_list.html` to render a small visual indicator on rows for expenses flagged by T044a as recurring-sourced (FR-017) (depends on: T044a)
- [ ] T046 [P] [US4] Create `app/templates/recurring_occurrence_adjust.html`: form pre-filled with the occurrence's template values, editable before adding
- [ ] T047 [US4] Register the recurring router in `app/main.py` (depends on: T041–T044)

**Checkpoint**: User Stories 1–4 all work independently.

---

## Phase 7: User Story 5 - Manage an Existing Recurring Expense (Priority: P3)

**Goal**: A logged-in user can edit an active template's amount/category/description or cancel it, without disturbing already-confirmed expenses.

**Independent Test**: Edit a template's amount; confirm a not-yet-actioned pending occurrence reflects it while an already-confirmed expense doesn't. Cancel it; confirm no further occurrences appear.

### Tests for User Story 5

> Write these tests FIRST; confirm they FAIL before implementation

- [ ] T048 [P] [US5] Test editing an active template's amount/category/description updates a not-yet-actioned pending occurrence's values, while an already-confirmed expense keeps its original values, in `tests/test_recurring.py::test_edit_template_affects_only_pending`
- [ ] T049 [P] [US5] Test canceling an active template removes its unconfirmed pending occurrences and produces no further ones, while previously confirmed expenses remain, in `tests/test_recurring.py::test_cancel_template`
- [ ] T050 [P] [US5] Test editing or canceling another user's template is rejected, in `tests/test_recurring.py::test_manage_template_isolation`

### Implementation for User Story 5

- [ ] T051 [US5] Implement `POST /recurring/{template_id}/edit` in `app/routers/recurring.py`: update amount/category/description in place, scoped to `current_user.id` (frequency not accepted, FR-014a) (depends on: T040, T041)
- [ ] T052 [US5] Implement `POST /recurring/{template_id}/cancel` in `app/routers/recurring.py`: set status to canceled, scoped to `current_user.id` (depends on: T041)
- [ ] T053 [P] [US5] Extend `app/templates/recurring_list.html` with edit/cancel controls per active template (depends on: T045)

**Checkpoint**: All five user stories are independently functional; the full feature is complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span multiple user stories

- [ ] T054 [P] Audit every new/changed route in `app/routers/expenses.py` and `app/routers/recurring.py` to confirm all reads/writes are scoped to `current_user.id` (FR-008, FR-016)
- [ ] T055 Run the [quickstart.md](./quickstart.md) validation scenarios end-to-end against `docker compose up --build`
- [ ] T056 Run the full `pytest` suite via `docker compose --profile test run --rm --build test pytest` against the real PostgreSQL service and confirm all tests pass (Constitution Principle II)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; confirms nothing further is needed
- **Foundational (Phase 2)**: Depends on Setup completion; BLOCKS all user stories
- **User Stories (Phase 3–7)**: All depend on Foundational phase completion
  - US1 and US2 are both P1 and both depend only on T005 (the shared `ExpenseForm` change); they can proceed in parallel
  - US3 depends on T005 and reuses `expense_form.html`/`ExpenseForm`, but its own route/tests are independent of US1/US2's completion
  - US4 depends on T002–T004 (the new tables) rather than on US1–US3
  - US5 depends on US4 (edits/cancels the templates US4 creates)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational (T005) only.
- **US2 (P1)**: Foundational (T005) only. Independent of US1 (both extend the same route/schema but touch different validation rules).
- **US3 (P1)**: Foundational (T005) + reuses `expense_form.html` (extended by T009 from US1, per T024's dependency).
- **US4 (P2)**: Foundational (T002–T004). Independent of US1–US3 aside from producing ordinary `Expense` rows.
- **US5 (P3)**: Foundational + US4 (edits/cancels US4's templates).

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution Principle I)
- Schemas/models before route handlers
- Route handlers before templates are wired in (templates marked [P] can be authored in parallel)
- Story complete and independently testable before moving to the next priority

### Parallel Opportunities

- Foundational model tasks T002/T003 can run in parallel
- All tests within a story marked [P] can run in parallel (independent test functions)
- Templates marked [P] (T045, T045a, T046) can be authored in parallel with their story's route-handler tasks
- US1 and US2 can be implemented in parallel once Foundational is done (both depend only on T005)

---

## Parallel Example: User Story 4

```bash
# Launch all tests for User Story 4 together:
Task: "Test POST /recurring creates an active template in tests/test_recurring.py::test_create_recurring_template"
Task: "Test POST /recurring rejects a non-positive amount in tests/test_recurring.py::test_create_recurring_template_rejects_non_positive_amount"
Task: "Test GET /recurring surfaces this month's pending occurrences in tests/test_recurring.py::test_pending_occurrences_current_month"
Task: "Test confirming an occurrence creates a matching expense in tests/test_recurring.py::test_confirm_occurrence"
Task: "Test the adjust-and-add path uses adjusted values in tests/test_recurring.py::test_adjust_and_add_occurrence"
Task: "Test skipping an occurrence creates no expense in tests/test_recurring.py::test_skip_occurrence"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL: blocks all stories)
3. Complete Phase 3: User Story 1 (Backdate)
4. Complete Phase 4: User Story 2 (Refund)
5. Complete Phase 5: User Story 3 (Edit)
6. **STOP and VALIDATE**: a user can backdate, refund, and edit within the current month end-to-end
7. Deploy/demo if ready: this is the full "retroactive editing" half of the feature, with standalone value

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → test independently → demo (backdating works)
3. US2 → test independently → demo (refunds work)
4. US3 → test independently → demo (editing works; retroactive-editing ask complete)
5. US4 → test independently → demo (recurring templates produce confirmable occurrences)
6. US5 → test independently → demo (full feature: recurring templates are manageable)
7. Polish → run quickstart.md end-to-end, full test suite green

### Parallel Team Strategy

With multiple developers, after Foundational is done:
- Developer A: US1 → US3 (US3 extends US1's template work)
- Developer B: US2 (independent of US1/US3 aside from the shared Foundational schema change)
- Developer C: US4 → US5 (sequential, since US5 manages US4's templates)

---

## Notes

- [P] tasks = independent files/functions, no dependencies
- [Story] label maps task to specific user story for traceability
- Verify each story's tests fail before implementing that story
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
