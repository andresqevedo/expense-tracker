# Quickstart: Expense Tracker MVP

Validates the feature end-to-end against the criteria in
[spec.md](./spec.md) Success Criteria. See [data-model.md](./data-model.md)
and [contracts/web-routes.md](./contracts/web-routes.md) for field-level
and route-level detail.

## Prerequisites

- Docker + Docker Compose (no other host dependency, per Constitution
  Principle V).
- A `.env` file in the repo root (copy from `.env.example`) providing at
  least `DATABASE_URL`/DB credentials and `JWT_SECRET_KEY`.

## Run the stack

```bash
docker compose up --build
```

This starts the `db` (PostgreSQL 16) and `app` (FastAPI) services. The
`app` container's entrypoint runs `alembic upgrade head` automatically
before starting the server, creating `users`, `categories`, `expenses`,
`budgets` and seeding the 7 fixed categories on first boot (a no-op on
later restarts once already up to date).

The app is now reachable at `http://localhost:8000`.

## Validation scenarios

1. **Register and reach an empty expense list** (US1, SC-001)
   - Visit `/register`, submit a new email + a password meeting the
     policy (≥ 8 chars, ≥ 1 letter, ≥ 1 digit).
   - Expect: redirected to `/expenses` and signed in (auth cookie set);
     the list shows the empty state.
   - Re-attempt registration with the same email → expect a rejection
     with no duplicate account created.
   - Log out, then log back in with the same credentials → expect
     success; with a wrong password → expect a generic rejection.

2. **Add an expense** (US2, SC-002)
   - From `/expenses/new`, submit a positive amount (e.g. `12.50`), a
     category, and today's date.
   - Expect: redirected to `/expenses`, the new entry visible.
   - Retry with a zero/negative amount, a missing category, or a
     non-today date → expect each rejected with an explanatory message
     and nothing saved.

3. **List expenses, scoped per user** (US3)
   - As a second, separately-registered user, add a different expense.
   - Expect: each user's `/expenses` shows only their own entries, most
     recent first; neither sees the other's data.

4. **Monthly totals by category** (US4, SC-003)
   - Add several expenses across at least two categories in the current
     month.
   - Visit `/summary` → expect each category's total to equal the exact
     sum of that user's expenses in that category for the month.
   - Switch `?month=` to a month with no expenses → expect the empty
     state.

5. **Budget vs. actual** (US5, SC-004)
   - On `/budgets`, set a budget for one category (e.g. `100.00`).
   - Add expenses in that category for the current month.
   - Reload `/budgets` → expect budgeted amount, actual amount, and
     difference shown, with a clear under/at/over indicator.
   - View a category with expenses but no budget → expect it labeled as
     having no budget, not compared against zero.
   - Update the budget amount, then check a **past** month's
     budget-vs-actual → expect the past month to still show the
     previously active amount, not the new one.

6. **Privacy check** (SC-005)
   - Across the two test users created above, confirm neither
     `/expenses`, `/summary`, nor `/budgets` for one account ever
     surfaces the other account's data, including by directly guessing
     an identifier in a URL if one is exposed.

## Automated tests

```bash
docker compose --profile test run --rm --build test pytest
```

The `app` service builds the lean `final` Dockerfile stage (no compiler, no
dev dependencies, no test files) and cannot run pytest; the `test` service
builds the `test` stage (adds the `dev` extras and `tests/`) and is gated
behind the `test` Compose profile so it never starts on a plain
`docker compose up`. `run` starts `db` (waiting for its healthcheck) if it
isn't already up and propagates pytest's real exit code; `--rm` cleans up
the test container afterward. Per Constitution Principle II, these run
against the real PostgreSQL service defined in `docker-compose.yml`, in a
dedicated `expense_tracker_test` database created and migrated by
`tests/conftest.py`, not SQLite or a mocked DB layer.

Once the suite passes, stop `db` with `docker compose stop` (not `down`,
which would remove the container) so nothing is left running in the
background.
