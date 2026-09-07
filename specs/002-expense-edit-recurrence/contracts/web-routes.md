# Contracts: Web Routes (Retroactive Editing and Recurring Transactions)

This extends spec 001's [web-routes.md](../../001-expense-tracker-mvp/contracts/web-routes.md)
contract style: server-rendered pages and form-submission routes, JWT
cookie auth, server-side validation as the source of truth. Only new or
changed routes are documented here; everything else from spec 001 is
unchanged.

## Expenses (changed and new)

| Method & Path | Auth | Request | Response | Spec refs |
|---|---|---|---|---|
| `GET /expenses/new` | required | (changed) date field now defaults to today but accepts any date within the current calendar month | Add-expense form | US1, US2 |
| `POST /expenses` | required | (changed) `amount` may now be negative (refund); `date` may be any day in `[current month start, today]`, not only today | 302 to `/expenses` on success (a negative amount gets "refund" auto-appended to `description` if absent, FR-004); 200 with field errors on a zero amount, missing category, or a date outside the current month or in the future | US1, US2; FR-001 through FR-004 |
| `GET /expenses/{expense_id}/edit` | required, owner only | path: `expense_id` | Edit form pre-filled with the expense's current values, if it belongs to the current user and its stored date is within the current calendar month; a not-found/403 response otherwise | US3; FR-005, FR-006, FR-008 |
| `POST /expenses/{expense_id}/edit` | required, owner only | `amount`, `category_id`, `date`, `description?` (form-encoded), same validation as `POST /expenses` | 302 to `/expenses` on success; 200 with field errors on invalid input; rejected (not-found/403) if the expense isn't the current user's or its stored date has left the current calendar month since the form was opened | US3; FR-005 through FR-008 |
| `GET /expenses` | required | (changed) unchanged request shape | Expense list, unchanged except each row now carries a small visual indicator when the expense originated from a confirmed/adjusted recurring occurrence; no effect on totals (FR-017, FR-017a) | US4; FR-017, FR-017a |

## Recurring Templates and Occurrences (new)

| Method & Path | Auth | Request | Response | Spec refs |
|---|---|---|---|---|
| `GET /recurring` | required | optional query params are not needed; always computed against the current calendar month | Page listing the user's active templates (each labeled with its computed recurrence pattern, FR-010b; canceled templates never appear, FR-015b), a form to create a new one, and this month's pending occurrences (empty state if none) | US4, US5; FR-010, FR-010b, FR-011, FR-015b |
| `POST /recurring` | required | `amount`, `category_id`, `description?`, `frequency` (`weekly`\|`monthly`\|`yearly`) (form-encoded) | 302 to `/recurring` on success; 200 with field errors on a non-positive amount (FR-010a), missing category, or invalid frequency | US4; FR-010, FR-010a |
| `POST /recurring/{template_id}/edit` | required, owner only | `amount`, `category_id`, `description?` (form-encoded); `frequency` is not accepted here (immutable, FR-014a) | 302 to `/recurring` on success (applies to occurrences not yet actioned this month, per FR-014); 200 with field errors on invalid input; rejected if the template isn't the current user's | US5; FR-014, FR-014a, FR-016 |
| `POST /recurring/{template_id}/cancel` | required, owner only | | 302 to `/recurring`; removes the template's unconfirmed pending occurrences from view, no further occurrences ever produced (FR-015); already-confirmed expenses unaffected | US5; FR-015 |
| `POST /recurring/{template_id}/occurrences/{due_date}/confirm` | required, owner only | path: `template_id`, `due_date` (`YYYY-MM-DD`) | 302 to `/recurring`; creates an expense with the template's current amount/category/description dated `due_date`, and records a `confirmed` action row; rejected (400/404) if `due_date` isn't a currently pending occurrence for that template (already actioned, not produced by the template's schedule, or outside the current month) | US4; FR-012, FR-013, FR-017 |
| `GET /recurring/{template_id}/occurrences/{due_date}/adjust` | required, owner only | path: `template_id`, `due_date` | Form pre-filled with the template's current amount/category/description and `due_date`, editable before adding | US4; FR-012 |
| `POST /recurring/{template_id}/occurrences/{due_date}/adjust` | required, owner only | `amount`, `category_id`, `date`, `description?` (form-encoded); same validation as `POST /expenses` (current month, non-future, non-zero amount, refund-tagging rule) | 302 to `/recurring` on success: creates an expense with the adjusted values and records a `confirmed` action row referencing it; 200 with field errors on invalid input, occurrence remains pending (FR-012 adjustment-failure rule) | US4; FR-012, FR-017 |
| `POST /recurring/{template_id}/occurrences/{due_date}/skip` | required, owner only | path: `template_id`, `due_date` | 302 to `/recurring`; records a `skipped` action row, no expense created, occurrence never offered again (FR-012, FR-013) | US4; FR-012, FR-013 |

## Cross-cutting

- Every `required`-auth route resolves the current user from the JWT and
  scopes all reads/writes to `user_id = current_user.id`; no route accepts
  another user's expense or recurring-template identifier (FR-008, FR-016).
- `due_date` path segments are validated as real dates produced by that
  specific template's frequency and anchor before any action is accepted;
  an arbitrary date that the template's schedule would never produce is
  rejected the same way an already-actioned one is.
- All `POST` routes validate input server-side regardless of any
  client-side HTML5 constraints, consistent with spec 001.
