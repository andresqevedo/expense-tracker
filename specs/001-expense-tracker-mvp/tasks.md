---

description: "Task list for Expense Tracker MVP implementation"
---

# Tasks: Expense Tracker MVP

**Input**: Design documents from `/specs/001-expense-tracker-mvp/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/web-routes.md](./contracts/web-routes.md), [quickstart.md](./quickstart.md)

**Tests**: Included. Constitution Principle I (Test-First Development) mandates a failing test committed before each route's implementation — this is not optional for this project.

**Organization**: Tasks are grouped by user story (from spec.md, in priority order P1 → P3) to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- File paths follow the structure in [plan.md](./plan.md) § Project Structure

## Path Conventions

Single backend project (no separate frontend — see plan.md § Structure Decision):
`app/` (application code), `alembic/` (migrations), `tests/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create the project skeleton directories per plan.md § Project Structure: `app/`, `app/models/`, `app/schemas/`, `app/security/`, `app/routers/`, `app/templates/`, `app/static/`, `alembic/versions/`, `tests/`
- [X] T002 Initialize `pyproject.toml` with Python 3.12 and dependencies: fastapi, uvicorn, sqlalchemy[asyncio]>=2.0, alembic, asyncpg, jinja2, python-multipart, pydantic>=2, pydantic-settings, python-jose[cryptography], passlib[bcrypt], pytest, pytest-asyncio, httpx
- [X] T003 [P] Write `docker-compose.yml` defining the `db` (postgres:16, named volume, healthcheck) and `app` (build from `Dockerfile`, depends_on db healthy, env from `.env`) services
- [X] T004 [P] Write `Dockerfile` for the FastAPI app (Python 3.12 base, install deps from pyproject.toml, run `uvicorn app.main:app`)
- [X] T005 [P] Write `.env.example` with `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM` placeholders; confirm `.env` is listed in `.gitignore`
- [X] T006 [P] Configure pytest (`pyproject.toml` `[tool.pytest.ini_options]` or `pytest.ini`): `asyncio_mode = auto`, `testpaths = ["tests"]`

**Checkpoint**: `docker compose build` succeeds (no runtime wiring yet).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement `app/config.py`: pydantic-settings `Settings` class reading `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM` from the environment
- [X] T008 Implement `app/db/base.py` (declarative `Base`) and `app/db/session.py` (async engine from `Settings.DATABASE_URL`, `async_sessionmaker`)
- [X] T009 Initialize Alembic in async mode (`alembic/env.py` wired to `app.db.base.Base.metadata` and the async engine); configure `alembic.ini` to read `DATABASE_URL` from the environment
- [X] T010 [P] Create `User` model in `app/models/user.py` per data-model.md § User (UUID PK, unique email, password_hash, created_at)
- [X] T011 [P] Create `Category` model in `app/models/category.py` per data-model.md § Category (int PK, unique name)
- [X] T012 [P] Create `Expense` model in `app/models/expense.py` per data-model.md § Expense (UUID PK, user_id FK, category_id FK, amount numeric(10,2), date, description, created_at)
- [X] T013 [P] Create `Budget` model in `app/models/budget.py` per data-model.md § Budget (UUID PK, user_id FK, category_id FK, effective_month, amount numeric(10,2), created_at; unique on user_id+category_id+effective_month)
- [X] T014 Generate and write the initial Alembic migration `alembic/versions/0001_initial_schema.py` creating the users, categories, expenses, budgets tables and seeding the 7 fixed categories (Food, Transportation, Housing, Utilities, Entertainment, Health, Other) (depends on: T009, T010, T011, T012, T013)
- [X] T015 [P] Implement `app/security/passwords.py`: `hash_password` / `verify_password` using passlib bcrypt, enforcing the ≥8-char + letter + digit policy (FR-001a)
- [X] T016 [P] Implement `app/security/jwt.py`: `create_access_token`, `decode_access_token`, and a helper to extract the token from the `access_token` HttpOnly cookie (falling back to an `Authorization: Bearer` header) per research.md § 1
- [X] T017 Implement `app/dependencies.py`: `get_db` (yields an `AsyncSession`) and `get_current_user` (resolves the JWT via app/security/jwt.py and loads the `User`, raising/redirecting when absent or invalid) (depends on: T008, T016)
- [X] T018 Implement `app/main.py`: FastAPI app factory, Jinja2Templates + StaticFiles mounts, router registration placeholder, global exception handler stub (depends on: T007, T008)
- [X] T019 [P] Create `app/templates/base.html` (shared layout/nav) and `app/static/styles.css` (plain CSS)
- [X] T020 Implement `tests/conftest.py`: async engine/session fixtures against the real PostgreSQL service from `docker-compose.yml` (a dedicated test database), a fixture that runs Alembic migrations once per test session, per-test transaction rollback for isolation, and an `httpx.AsyncClient` (`ASGITransport`) fixture wired to the app with `get_db` overridden — per Constitution Principle II and research.md § 5 (depends on: T008, T014, T018)

**Checkpoint**: Foundation ready — `docker compose up --build`, `alembic upgrade head`, and an empty `pytest` collection all succeed. User story implementation can now begin.

---

## Phase 3: User Story 1 - Register and Log In (Priority: P1) 🎯 MVP

**Goal**: A visitor can register with email/password and a returning user can log back in to reach their own private data.

**Independent Test**: Register a new account, log out, log back in with the same credentials.

### Tests for User Story 1

> Write these tests FIRST; confirm they FAIL before implementation (Constitution Principle I)

- [X] T021 [P] [US1] Test `POST /register` creates an account and signs the visitor in; a duplicate email is rejected with no duplicate account created, in `tests/test_auth.py::test_register_and_duplicate_email`
- [X] T022 [P] [US1] Test `POST /register` rejects a password under 8 characters, or missing a letter or digit, with an explanatory error and no account created, in `tests/test_auth.py::test_register_weak_password`
- [X] T023 [P] [US1] Test `POST /login` signs in a registered user with correct credentials and rejects an incorrect password with a generic (non-field-specific) error, in `tests/test_auth.py::test_login_success_and_failure`
- [X] T024 [P] [US1] Test `POST /logout` ends the session (subsequent request to a protected route is unauthenticated), in `tests/test_auth.py::test_logout`
- [X] T025 [P] [US1] Test a registered user's `id` is a server-generated identifier distinct from their email, in `tests/test_auth.py::test_user_id_not_email`

### Implementation for User Story 1

- [X] T026 [US1] Create `app/schemas/auth.py`: `RegisterForm` (email + password, password policy validated) and `LoginForm` (email + password) Pydantic models
- [X] T027 [US1] Implement `GET /register` and `POST /register` in `app/routers/auth.py`: hash password (T015), insert `User`, set the JWT auth cookie, redirect to `/expenses`; re-render the form with field errors on duplicate email or weak password (depends on: T010, T015, T016, T026)
- [X] T028 [US1] Implement `GET /login` and `POST /login` in `app/routers/auth.py`: verify credentials, set the JWT auth cookie, redirect to `/expenses`; re-render with a generic error on failure (depends on: T010, T015, T016, T026)
- [X] T029 [US1] Implement `POST /logout` in `app/routers/auth.py`: clear the auth cookie, redirect to `/login` (depends on: T017)
- [X] T030 [P] [US1] Create `app/templates/register.html` and `app/templates/login.html`
- [X] T031 [US1] Register the auth router in `app/main.py` (depends on: T018, T027, T028, T029)

**Checkpoint**: User Story 1 is fully functional and independently testable — register, log out, log back in.

---

## Phase 4: User Story 2 - Add an Expense (Priority: P1)

**Goal**: A logged-in user records an expense (amount, category, date, optional description) attributed to their account.

**Independent Test**: Log in, submit a new expense, confirm it is saved and associated with that user.

### Tests for User Story 2

> Write these tests FIRST; confirm they FAIL before implementation

- [X] T032 [P] [US2] Test `POST /expenses` saves an expense with a positive amount, category, and today's date, attributed to the logged-in user, in `tests/test_expenses.py::test_add_expense_success`
- [X] T033 [P] [US2] Test `POST /expenses` rejects a zero, negative, or missing amount with an explanatory error, in `tests/test_expenses.py::test_add_expense_invalid_amount`
- [X] T034 [P] [US2] Test `POST /expenses` rejects a submission with no category selected, in `tests/test_expenses.py::test_add_expense_missing_category`
- [X] T035 [P] [US2] Test `POST /expenses` rejects a future date, a past date, and a non-date value, in `tests/test_expenses.py::test_add_expense_invalid_date`
- [X] T036 [P] [US2] Test `POST /expenses` truncates an amount submitted with more than 2 decimal places to 2 decimal places rather than rejecting it (FR-007a; e.g. `12.345` → `12.34`), in `tests/test_expenses.py::test_add_expense_amount_truncation`

### Implementation for User Story 2

- [X] T037 [US2] Create `app/schemas/expense.py`: `ExpenseForm` validating positive amount (with truncation to 2 decimals per FR-007a), required category, date == today
- [X] T038 [US2] Implement `GET /expenses/new` and `POST /expenses` (create) in `app/routers/expenses.py`: category options from the `Category` table, insert `Expense` scoped to `current_user`, redirect to `/expenses`; re-render with field errors on validation failure (depends on: T012, T017, T037)
- [X] T039 [P] [US2] Create `app/templates/expense_form.html`
- [X] T040 [US2] Register the expenses router in `app/main.py` (depends on: T018, T038)

**Checkpoint**: User Stories 1 AND 2 both work independently — register/login, then add an expense.

---

## Phase 5: User Story 3 - List Expenses (Priority: P2)

**Goal**: A logged-in user views their own recorded expenses, most recent first, scoped strictly to their account.

**Independent Test**: Log in as a user with existing expenses; confirm the list shows exactly that user's expenses in a sensible order, with no other user's data visible.

### Tests for User Story 3

> Write these tests FIRST; confirm they FAIL before implementation

- [X] T041 [P] [US3] Test `GET /expenses` lists a user's expenses most-recent-first (date desc, then created_at desc), in `tests/test_expenses.py::test_list_expenses_order`
- [X] T042 [P] [US3] Test `GET /expenses` shows a clear empty state for a user with no recorded expenses, in `tests/test_expenses.py::test_list_expenses_empty`
- [X] T043 [P] [US3] Test `GET /expenses` for one user never includes another user's expenses, in `tests/test_expenses.py::test_list_expenses_isolation`

### Implementation for User Story 3

- [X] T044 [US3] Implement `GET /expenses` (list) in `app/routers/expenses.py`: query `Expense` filtered to `current_user.id`, ordered by date desc/created_at desc (depends on: T012, T017, T038)
- [X] T045 [P] [US3] Extend `app/templates/expenses_list.html` with the populated list and empty-state markup

**Checkpoint**: User Stories 1–3 all work independently.

---

## Phase 6: User Story 4 - Monthly Totals by Category (Priority: P2)

**Goal**: A logged-in user views their expenses for a selected month grouped by category, with a total per category.

**Independent Test**: Log in as a user with expenses across categories in the same month; confirm each category's displayed total equals the exact sum of that user's expenses in that category for that month.

### Tests for User Story 4

> Write these tests FIRST; confirm they FAIL before implementation

- [X] T046 [P] [US4] Test `GET /summary` returns the correct per-category sum for the current month across multiple categories, in `tests/test_summary.py::test_summary_totals`
- [X] T047 [P] [US4] Test `GET /summary?month=YYYY-MM` recalculates totals for a selected past month, in `tests/test_summary.py::test_summary_month_switch`
- [X] T048 [P] [US4] Test `GET /summary` shows a clear empty state (no category totals) for a month with no expenses, in `tests/test_summary.py::test_summary_empty_month`
- [X] T068 [P] [US4] Test `GET /summary` for one user never includes another user's expenses in its totals, in `tests/test_summary.py::test_summary_isolation`

### Implementation for User Story 4

- [X] T049 [US4] Implement `GET /summary` in `app/routers/summary.py`: `SUM(amount)` grouped by `category_id`, filtered to `current_user.id` and the selected month (default current month), joined to category names (depends on: T012, T017)
- [X] T050 [P] [US4] Create `app/templates/summary.html`
- [X] T051 [US4] Register the summary router in `app/main.py` (depends on: T018, T049)

**Checkpoint**: User Stories 1–4 all work independently.

---

## Phase 7: User Story 5 - Budget vs. Actual (Priority: P3)

**Goal**: A logged-in user sets a monthly budget per category and views actual spend against it, per month, with under/at/over status.

**Independent Test**: Set a budget for one category, record expenses in that category within a month, confirm the comparison view correctly shows actual vs. budgeted and flags over/under/at.

### Tests for User Story 5

> Write these tests FIRST; confirm they FAIL before implementation

- [X] T052 [P] [US5] Test `POST /budgets` sets a budget that applies to the current and future months, in `tests/test_budgets.py::test_set_budget`
- [X] T053 [P] [US5] Test `GET /budgets` shows budgeted amount, actual amount, difference, and a clear under/at/over status, in `tests/test_budgets.py::test_budget_comparison`
- [X] T054 [P] [US5] Test `GET /budgets` shows a category with expenses but no budget as "no budget set" rather than compared against zero, in `tests/test_budgets.py::test_budget_none_set`
- [X] T055 [P] [US5] Test `POST /budgets` submitted twice within the same month updates that month's value rather than creating a duplicate history entry, in `tests/test_budgets.py::test_budget_update_same_month`
- [X] T056 [P] [US5] Test updating a budget in the current month leaves a previously-viewed past month's resolved budget unchanged, in `tests/test_budgets.py::test_budget_history_preserves_past_month`
- [X] T057 [P] [US5] Test a budget amount submitted with more than 2 decimal places is truncated to 2 (FR-007a), in `tests/test_budgets.py::test_budget_amount_truncation`
- [X] T069 [P] [US5] Test `GET /budgets` for one user never includes another user's budgets or expense totals, in `tests/test_budgets.py::test_budget_isolation`

### Implementation for User Story 5

- [X] T058 [US5] Create `app/schemas/budget.py`: `BudgetForm` validating a positive amount (with truncation to 2 decimals per FR-007a) and a required category
- [X] T059 [US5] Implement the budget resolution helper in `app/routers/budgets.py` (or `app/services/budgets.py`): for a given user/category/month, select the row with the greatest `effective_month <= target month` (data-model.md § Budget resolution rule) (depends on: T013)
- [X] T060 [US5] Implement `GET /budgets` and `POST /budgets` in `app/routers/budgets.py`: `POST` upserts the current month's effective row; `GET` renders, per category, the resolved budget (via T059), actual monthly total (reusing the summary computation from T049), difference, and status (depends on: T017, T049, T058, T059)
- [X] T061 [P] [US5] Create `app/templates/budget.html`
- [X] T062 [US5] Register the budgets router in `app/main.py` (depends on: T018, T060)

**Checkpoint**: All five user stories are independently functional — the full MVP is complete.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that span multiple user stories

- [X] T063 [P] Implement a shared form-validation-error rendering pattern (e.g. a Jinja2 macro/exception handler) in `app/main.py` so every `POST` route re-renders its form with field errors consistently
- [X] T064 [P] Audit every route in `app/routers/*.py` to confirm all reads/writes are scoped to `current_user.id` (FR-010) — no route accepts another user's identifier for expenses or budgets
- [X] T065 Run the [quickstart.md](./quickstart.md) validation scenarios end-to-end against `docker compose up --build`
- [X] T066 [P] Confirm `docker compose up --build` requires no host dependency beyond Docker (Constitution Principle V) — fresh clone + `.env` from `.env.example` only
- [X] T067 Run the full `pytest` suite via `docker compose --profile test run --rm --build test pytest` against the real PostgreSQL service and confirm all tests pass (Constitution Principle II)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3–7)**: All depend on Foundational phase completion
  - US1 and US2 are both P1; US2's expense creation requires an authenticated user, so US1 should be implemented first even though both are P1
  - US3 (list) depends on US2 having created the `POST /expenses` handler/router file it extends (T038/T040), though its own tests are independent
  - US4 (summary) depends only on the `Expense` model (Foundational) — independent of US2/US3's routes, though it needs expense data to be meaningful
  - US5 (budget) depends on US4's monthly-total computation (T049) being available to reuse for "actual" spend
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Foundational only. No dependency on other stories.
- **US2 (P1)**: Foundational + US1 (needs an authenticated user to attribute expenses to).
- **US3 (P2)**: Foundational + US2 (extends the expenses router/template US2 creates).
- **US4 (P2)**: Foundational + US2 (needs expense data to aggregate); route itself is independent of US3.
- **US5 (P3)**: Foundational + US4 (reuses the monthly-total computation as "actual" spend).

### Within Each User Story

- Tests MUST be written and FAIL before implementation (Constitution Principle I)
- Schemas before route handlers
- Route handlers before templates are wired in (though templates marked [P] can be authored in parallel)
- Story complete and independently testable before moving to the next priority

### Parallel Opportunities

- All Setup tasks marked [P] (T003–T006) can run in parallel
- Foundational model tasks T010–T013 can run in parallel; T015/T016 can run in parallel with each other and with the models
- All tests within a story marked [P] can run in parallel (they touch different test functions/files)
- Templates marked [P] (T030, T039, T045, T050, T061) can be authored in parallel with their story's route-handler task

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Test POST /register creates an account and rejects duplicate email in tests/test_auth.py::test_register_and_duplicate_email"
Task: "Test POST /register rejects a weak password in tests/test_auth.py::test_register_weak_password"
Task: "Test POST /login succeeds and rejects wrong password generically in tests/test_auth.py::test_login_success_and_failure"
Task: "Test POST /logout ends the session in tests/test_auth.py::test_logout"
Task: "Test a registered user's id is not their email in tests/test_auth.py::test_user_id_not_email"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Register/Login)
4. Complete Phase 4: User Story 2 (Add an Expense)
5. **STOP and VALIDATE**: an authenticated user can add an expense end-to-end
6. Deploy/demo if ready — this is the smallest slice with standalone value

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. US1 → test independently → demo (accounts work)
3. US2 → test independently → demo (MVP: accounts + expense capture)
4. US3 → test independently → demo (users can review their spending)
5. US4 → test independently → demo (monthly insight)
6. US5 → test independently → demo (full MVP: budget vs. actual)
7. Polish → run quickstart.md end-to-end, full test suite green

### Parallel Team Strategy

With multiple developers, after Foundational is done:
- Developer A: US1 → US2 (sequential, since US2 depends on US1)
- Developer B: US4 (independent of US1–US3 aside from the shared `Expense` model already in Foundational)
- Once US2 and US4 land: Developer C picks up US3 (extends US2) and US5 (extends US4)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Verify each story's tests fail before implementing that story
- Commit after each task or logical group
- Stop at any checkpoint to validate a story independently
- Avoid: vague tasks, same-file conflicts, cross-story dependencies that break independence
