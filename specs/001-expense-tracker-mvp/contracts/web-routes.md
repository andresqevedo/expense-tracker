# Contracts: Web Routes

This app exposes a server-rendered web interface (Jinja2 + plain CSS), not
a standalone JSON API, so its "contract" is the set of HTTP routes: page
(`GET`) routes that render HTML, and form-submission (`POST`) routes that
process input and redirect or re-render with errors. Auth is a JWT stored
in an `HttpOnly` cookie (see [research.md](../research.md) §1); a request
with no valid cookie/`Authorization` header is redirected to `/login` for
protected routes.

## Auth

| Method & Path | Auth | Request | Response | Spec refs |
|---|---|---|---|---|
| `GET /register` | none | — | Registration form | US1 |
| `POST /register` | none | `email`, `password` (form-encoded) | 302 → `/expenses` + sets auth cookie on success; 200 + form re-rendered with field errors on duplicate email (FR-002) or weak password (FR-001a) | US1 scenarios 1-2, 6; FR-001, FR-001a, FR-002 |
| `GET /login` | none | — | Login form | US1 |
| `POST /login` | none | `email`, `password` (form-encoded) | 302 → `/expenses` + sets auth cookie on success; 200 + generic "invalid email or password" error on failure (no field-specific hint) | US1 scenarios 3-4; FR-003, FR-004 |
| `POST /logout` | required | — | 302 → `/login`, clears auth cookie | FR-005 |

## Expenses

| Method & Path | Auth | Request | Response | Spec refs |
|---|---|---|---|---|
| `GET /expenses` | required | — (no month filter; always the user's full expense history) | Expense list page, most recent first (empty state if none) | US3; FR-009, FR-010 |
| `GET /expenses/new` | required | — | Add-expense form (category options = the 7 fixed categories; date defaults to, and is fixed at, today) | US2 |
| `POST /expenses` | required | `amount`, `category_id`, `date`, `description?` (form-encoded); `amount` submitted with more than 2 decimal places is rounded down to 2 before validation/storage (FR-007a) | 302 → `/expenses` on success; 200 + form re-rendered with field errors on non-positive amount, missing category, or date ≠ today/invalid | US2 scenarios 1-4; FR-006, FR-007, FR-007a, FR-008 |

## Monthly Summary

| Method & Path | Auth | Request | Response | Spec refs |
|---|---|---|---|---|
| `GET /summary` | required | optional `?month=YYYY-MM` (defaults to current month) | Per-category totals for that month (empty state if none) | US4; FR-011 |

## Budgets

| Method & Path | Auth | Request | Response | Spec refs |
|---|---|---|---|---|
| `GET /budgets` | required | optional `?month=YYYY-MM` (defaults to current month) | Budget-vs-actual page: for each category, budgeted amount (or "no budget set"), actual, difference, status; form to set/update a budget | US5; FR-014, FR-015 |
| `POST /budgets` | required | `category_id`, `amount` (form-encoded) | 302 → `/budgets` on success (writes/updates the current month's effective budget row per data-model.md); 200 + field errors on invalid amount | US5 scenarios 1-3; FR-012, FR-013 |

## Cross-cutting

- Every `required`-auth route resolves the current user from the JWT and
  scopes all reads/writes to `user_id = current_user.id`; no route accepts
  another user's identifier for expenses or budgets (FR-010).
- All `POST` routes validate input server-side regardless of any
  client-side HTML5 constraints (`required`, `type=number`, `type=date`
  attributes are a UX aid only, not the source of truth).
