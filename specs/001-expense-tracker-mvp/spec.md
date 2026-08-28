# Feature Specification: Expense Tracker MVP

**Feature Branch**: `001-expense-tracker-mvp`

**Created**: 2026-08-27

**Status**: Draft

**Input**: User description: "I need you to build a spec for the MVP. MVP scope: register/login, add expense, list expenses, monthly totals by category, budget vs. actual."

## Clarifications

### Session 2026-08-27

- Q: What is the complete, fixed list of expense categories for this MVP? → A: Exactly: Food, Transportation, Housing, Utilities, Entertainment, Health, Other (7 categories, nothing more)
- Q: When a user sets a new budget for a category that already has a budget for the currently-viewed month, does the new amount replace the old one for that same month too, or only for future months? → A: Per-month budget history — updating only affects the current month and future months; past months keep the value that was active then
- Q: Should the system reject an expense submission whose date is in the future, or is any date (past, present, or future) allowed? → A: Reject any date other than today (no past, no future); also reject any value that is not a valid date
- Q: What are the minimum password requirements for registration? → A: Minimum 8 characters plus at least one letter and one number
- Q: How should amounts (expense amounts and budget amounts) be handled for decimal precision? → A: Exactly 2 decimal places (e.g., 12.34); more precision is rejected, fewer is padded

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Register and Log In (Priority: P1)

A new user creates an account with an email and password, and a returning
user logs back in to reach their own private expense data. Every other
capability in this MVP depends on the user having an authenticated
identity, since expenses and budgets belong to a specific person.

**Why this priority**: Nothing else in the product is reachable or
meaningful without an account. This is the foundational capability that
must exist before any other story can be demonstrated end-to-end.

**Independent Test**: Can be fully tested by registering a new account with
an email and password, logging out, and logging back in with the same
credentials — delivering the value of a private, returnable account.

**Acceptance Scenarios**:

1. **Given** no existing account for an email address, **When** a visitor
   submits that email with a valid password, **Then** a new account is
   created and the visitor is signed in.
2. **Given** an email address that is already registered, **When** a
   visitor tries to register with that same email, **Then** registration is
   rejected with a clear message and no duplicate account is created.
3. **Given** a registered account, **When** the user logs in with the
   correct email and password, **Then** they are signed in and taken to
   their own expense data.
4. **Given** a registered account, **When** the user logs in with an
   incorrect password, **Then** login is rejected and no session is
   created.
5. **Given** several registered accounts, **Then** each account has to have
   a unique identifier that is not the email itself for the purposes of data 
   storage in the database.
6. **Given** no existing account for an email address, **When** a visitor
   submits that email with a password shorter than 8 characters, or one
   missing a letter or a number, **Then** registration is rejected and the
   password requirement is explained, and no account is created.

---

### User Story 2 - Add an Expense (Priority: P1)

A logged-in user records a new expense by entering an amount, a category,
and a date, so that it is saved to their personal expense history.

**Why this priority**: Capturing expenses is the core value the product
exists to deliver — without it there is no data to list, total, or compare
against a budget.

**Independent Test**: Can be fully tested by logging in, submitting a new
expense with an amount, category, and date, and confirming it is saved and
associated with that user's account.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they submit an expense with a
   positive amount, a category, and a date, **Then** the expense is saved
   and attributed to their account.
2. **Given** a logged-in user, **When** they submit an expense with a zero,
   negative, or missing amount, **Then** the system rejects the submission
   and explains what needs to be corrected.
3. **Given** a logged-in user, **When** they submit an expense without
   selecting a category, **Then** the system rejects the submission and
   explains what needs to be corrected.
4. **Given** a logged-in user, **When** they submit an expense dated in the
   future, in the past, or with an invalid (non-date) value, **Then** the
   system rejects the submission and explains that the date must be
   today's date.

---

### User Story 3 - List Expenses (Priority: P2)

A logged-in user views a list of their own recorded expenses, so they can
review what they have spent and when.

**Why this priority**: Once expenses can be captured, users need to see
them back to trust the data and get value from having recorded it; this
also underpins the totals and budget-comparison stories.

**Independent Test**: Can be fully tested by logging in as a user with
existing expenses and confirming the list shows exactly that user's
expenses, in a sensible order, with no other user's data visible.

**Acceptance Scenarios**:

1. **Given** a logged-in user with recorded expenses, **When** they open
   their expense list, **Then** they see each expense's amount, category,
   and date, most recent first.
2. **Given** a logged-in user with no recorded expenses, **When** they open
   their expense list, **Then** they see a clear empty state instead of an
   error or a blank screen.
3. **Given** two different user accounts each with their own expenses,
   **When** one user views their expense list, **Then** they see only
   their own expenses and never the other user's.

---

### User Story 4 - Monthly Totals by Category (Priority: P2)

A logged-in user views their expenses for a given month grouped by
category, with a total for each category, so they can see where their
money went that month.

**Why this priority**: Aggregated totals turn raw entries into the insight
the product promises, and this same aggregation is the basis for comparing
actual spending against a budget.

**Independent Test**: Can be fully tested by logging in as a user with
several expenses across categories in the same month and confirming each
category's displayed total equals the sum of that user's expenses in that
category for that month.

**Acceptance Scenarios**:

1. **Given** a logged-in user with expenses in multiple categories within
   the current month, **When** they view the monthly summary, **Then**
   each category shows the correct sum of that month's expenses in that
   category.
2. **Given** a logged-in user, **When** they select a different past
   month, **Then** the summary recalculates to show that month's totals by
   category.
3. **Given** a logged-in user with no expenses in a given month, **When**
   they view that month's summary, **Then** they see a clear empty state
   with no category totals.

---

### User Story 5 - Budget vs. Actual (Priority: P3)

A logged-in user sets a monthly budget amount for a category and, for any
given month, sees how their actual spending in that category compares to
the budget — including whether they are under, at, or over budget.

**Why this priority**: This is the highest-level insight in the MVP and
depends on both expense capture and monthly category totals already
existing, so it is the last piece layered on top.

**Independent Test**: Can be fully tested by logging in, setting a budget
for one category, recording expenses in that category within a month, and
confirming the comparison view correctly shows actual spend versus the
budgeted amount and flags whether the category is over budget.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they set a monthly budget amount
   for a category, **Then** that budget is saved and applies to the
   current month and any future month for that category until changed
   again.
2. **Given** a category with a monthly budget and some recorded expenses in
   the current month, **When** the user views the budget comparison,
   **Then** they see the budgeted amount, the actual amount spent, and the
   difference, clearly indicating whether they are over or under budget.
3. **Given** a category with recorded expenses but no budget set, **When**
   the user views the budget comparison, **Then** that category is shown
   as having no budget rather than being compared against zero.

---

### Edge Cases

- What happens when a user tries to register with an invalid email format?
  (Password minimum strength is defined in FR-001a.)
- How does the system handle a user attempting to view, edit, or delete
  another user's expense or budget directly (e.g., by guessing an
  identifier)?
- When a category's actual spending exactly equals its budget (both
  compared at 2 decimal places, per FR-007), the difference is 0.00 and
  the category is shown as exactly on budget (neither over nor under).
- What happens when a user requests a monthly summary or budget comparison
  for a month with no budgets and no expenses at all?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a visitor to register a new account using
  an email address and a password.
- **FR-001a**: System MUST reject a registration password that is shorter
  than 8 characters, or that lacks at least one letter or at least one
  number, and MUST indicate what is invalid.
- **FR-002**: System MUST reject registration attempts using an email
  address that already has an account.
- **FR-003**: System MUST allow a registered user to log in using their
  email address and password.
- **FR-004**: System MUST reject login attempts with an incorrect email
  and password combination without revealing which field was wrong.
- **FR-005**: System MUST allow a logged-in user to log out, ending their
  session.
- **FR-006**: System MUST allow a logged-in user to record a new expense
  consisting of an amount, a category, and a date, with an optional
  description.
- **FR-007**: System MUST reject an expense submission that has a
  non-positive amount, an amount with more than 2 decimal places, a
  missing category, a missing date, an invalid (non-date) date value, or a
  date other than the current day, and MUST indicate what is invalid.
- **FR-008**: System MUST associate every recorded expense with exactly
  the user who created it.
- **FR-009**: System MUST allow a logged-in user to view a list of their
  own recorded expenses, ordered from most recent to oldest.
- **FR-010**: System MUST NOT show a user any expense or budget belonging
  to another user.
- **FR-011**: System MUST allow a logged-in user to view, for a selected
  month, the total amount spent per category during that month.
- **FR-012**: System MUST allow a logged-in user to set a monthly budget
  amount for a category.
- **FR-013**: System MUST allow a logged-in user to update a category's
  budget amount, with the new amount applying to the current month and any
  future month, while any past month keeps the budget amount that was
  active for that category during that month.
- **FR-014**: System MUST allow a logged-in user to view, for a selected
  month and category, the budgeted amount, the actual amount spent, and
  the difference between them.
- **FR-015**: System MUST clearly distinguish a category with no budget
  set from a category that is exactly on budget or under budget.
- **FR-016**: System MUST persist all accounts, expenses, and budgets so
  they remain available across sessions.

### Key Entities

- **User**: A person with a private account, identified by a unique email
  address and a password credential. Owns all of their own expenses and
  budgets; no other user can see or modify them.
- **Expense**: A single recorded transaction belonging to one user,
  consisting of an amount (a positive value with exactly 2 decimal
  places), a category, a date, and an optional description. Used to
  compute monthly per-category totals.
- **Category**: A named grouping used to classify expenses and budgets.
  The fixed set, shared across all users and not owned by any one user, is
  exactly: Food, Transportation, Housing, Utilities, Entertainment, Health,
  Other.
- **Budget**: A monthly spending limit set by one user for one category,
  tracked per month so that editing a category's budget changes the
  current and future months' limit while past months retain the amount
  that was active for them at the time. Compared against that user's
  actual expense total in the same category and month to produce the
  budget-vs-actual view.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new visitor can register an account and reach their
  (empty) expense list in under 2 minutes.
- **SC-002**: A logged-in user can record a new expense in under 30
  seconds from opening the add-expense action to seeing it confirmed.
- **SC-003**: 100% of a user's recorded expenses for a given month are
  reflected in that month's category totals, with no discrepancy between
  the sum of individual expenses and the displayed total.
- **SC-004**: A user can determine, at a glance and without doing their
  own math, whether each budgeted category is under, at, or over budget
  for the selected month.
- **SC-005**: A user's data remains fully private: across testing, 0% of
  expenses or budgets created by one account are ever visible to another
  account.
- **SC-006**: 90% of first-time users can complete the full journey —
  register, add an expense, view the monthly total, and view a budget
  comparison — without external help or documentation.

## Assumptions

- Expense categories are a fixed, predefined set shared by all users for
  this MVP (Food, Transportation, Housing, Utilities, Entertainment,
  Health, Other); users cannot create custom categories yet.
- The app operates in a single currency; no multi-currency or currency
  conversion support is included in this MVP.
- A monthly budget set for a category applies to that category each month
  going forward until the user changes it, rather than requiring the user
  to re-enter it every month; changing it does not alter the budget amount
  recorded for months that have already passed.
- Password reset / "forgot password" flows, social login, and multi-factor
  authentication are out of scope for this MVP; only direct email/password
  registration and login are included.
- Editing or deleting an already-recorded expense is out of scope for this
  MVP; only adding and listing expenses is included.
- Each user's data (expenses and budgets) is private to that user; there is
  no sharing, household, or multi-user grouping in this MVP.
- Standard web application expectations apply for performance and error
  handling (fast responses, friendly validation messages) unless otherwise
  specified.
