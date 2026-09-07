# Feature Specification: Retroactive Expense Editing and Recurring Transactions

**Feature Branch**: `002-expense-edit-recurrence`

**Created**: 2026-09-07

**Status**: Draft

**Input**: User description: "I want to build a new feature that will allow to add expenses retroactively and modify old expenses (one good example is when a refund is given). Additionally, i want to allow a user to set up recurrent transactions."

## Clarifications

### Session 2026-09-07

- Q: How far back can a user backdate a new or edited expense? → A: Within the same calendar month only (protects prior months' closed budgets and totals from being altered).
- Q: Is deleting an expense in scope, to represent a full refund? → A: No deletion. A refund is instead recorded as a new expense with a negative amount; whenever an amount is negative, the description must contain the word "refund" (case-insensitive), appended automatically if the user didn't include it.
- Q: How are recurring occurrences generated? → A: Option C (user-confirmed), with a monthly cadence: when the user first visits in a new calendar month, every occurrence that template's frequency produces within that month appears as a pending item; each pending item is removed from the list once confirmed, skipped, or adjusted-and-added.
- Q: When should a pending occurrence be shown for a month the user never actively reviewed, or for a template created partway through the current month? → A: Current month only, stateless: each visit shows pending occurrences only for the current calendar month's due dates through today; a month never visited produces no backlog, and a template created mid-month still gets a pending occurrence for any of its due dates already passed that month.
- Q: Can a user change an active recurring template's frequency after creating it? → A: No. Frequency is fixed at creation and cannot be edited; a user who wants a different cadence cancels the template and creates a new one.
- Q: Should this feature's new routes meet the same server-side latency budget established by the MVP feature? → A: Yes. The existing 200ms default budget (from spec 001's Clarifications) extends to this feature's new routes, verified the same way via automated per-request latency assertions; none of these routes do password hashing, so none need the 500ms budget.
- Q: Can SC-006 ("90% of users can correctly predict...") be verified by an automated test? → A: No, user comprehension/prediction is not code-testable. Replaced with a system-behavior invariant that is: no expense attributed to a recurring template is ever created without an explicit user action (confirm or adjust-and-add).
- Q: What exactly does "current calendar month" mean (timezone basis, when it is evaluated)? → A: The same basis as spec 001 FR-007's definition of "today": the calendar month containing the server's UTC calendar day at the time of each request, evaluated fresh per request rather than cached or fixed at session start.
- Q: Does the adjust-and-add path on a pending occurrence have to obey the same date/amount/category rules as any other expense? → A: Yes. An adjusted occurrence is validated identically to a manually created or edited expense (FR-001 through FR-004): its date must fall within the current calendar month and not be in the future, and its amount must be non-zero with the refund-description rule applied when negative.
- Q: Can a recurring template's base amount be negative (a "recurring refund")? → A: No. A recurring template's amount must be positive; recurring refunds are not supported. A refund is always recorded as an ad hoc negative-amount expense (User Story 2), including via the adjust-and-add path on a pending occurrence if needed.
- Q: When FR-013 says an actioned occurrence is never offered again, is that permanent, or only for the remainder of the current calendar month? → A: Scoped to that month's list: once confirmed, adjusted-and-added, or skipped, an occurrence is removed from the current month's list and the action is final for that occurrence (no undo). A later month's occurrence from the same template is a separate, independent item, offered normally on its own schedule; that is not "the same item coming back," and it is unrelated to stopping the template altogether, which is what canceling it (FR-015) is for.
- Q: For a newly created recurring template, is its very first occurrence due on the creation date itself, or one interval later? → A: The creation date itself, for all three frequencies; each subsequent occurrence is one interval later. This generalizes the existing mid-month-creation edge case (a monthly template's already-passed anchor day still produces a pending occurrence the month it's created), now formalized as FR-011a.
- Q: Which requests should trigger pending-occurrence computation? → A: Route-local: only a request to `/recurring` or one of its occurrence-action routes (confirm, adjust, skip); nothing elsewhere in the app (e.g., `/expenses`) surfaces pending occurrences, matching how budgets/summary are already computed only on their own page.
- Q: Should the app tell the user which specific date(s) a template will recur on? → A: Yes, but only as a label on the template's row in `/recurring` after creation (e.g., "recurs on the 15th of each month"), not a separate live preview during the creation form itself.
- Q: After a user cancels a recurring template, should it remain visible anywhere? → A: No. It disappears entirely from `/recurring` once canceled; no historical/canceled-templates view exists, consistent with this project having no edit-history or audit-log UI elsewhere. Its previously confirmed expenses remain in the user's expense history regardless.
- Q: Should an expense created from a recurring occurrence show any visible indicator of its origin? → A: Yes. A small visual indicator appears in the expense list (FR-017a); totals and budget comparisons remain identical to a manually entered expense either way.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add an Expense for a Past Date (Priority: P1)

A logged-in user records an expense dated earlier than today but still within
the current calendar month, so they can catch up on spending they forgot to
log at the time.

**Why this priority**: Today's MVP rejects any expense whose date is not the
current day, so a user who forgets to log something even one day late has no
way to record it accurately. This is the smallest change that unblocks
accurate historical records.

**Independent Test**: Can be fully tested by logging in and submitting a new
expense dated earlier in the current month, then confirming it appears in
that month's expense list and totals.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they submit a new expense dated
   yesterday or any earlier date within the current calendar month, **Then**
   the expense is saved and appears in that month's totals.
2. **Given** a logged-in user, **When** they submit a new expense dated in a
   prior calendar month, **Then** the system rejects the submission and
   states that dates before the current month are not accepted.
3. **Given** a logged-in user, **When** they submit a new expense dated in
   the future, **Then** the system rejects the submission (unchanged from
   the existing today-only rule for future dates).

---

### User Story 2 - Record a Refund (Priority: P1)

A logged-in user records a refund by entering a new expense with a negative
amount in the relevant category, so their category totals and budget
comparison net the refund against prior spending without altering the
original expense.

**Why this priority**: Refunds are the explicit motivating example in this
feature's request. A negative-amount entry is the mechanism chosen to
represent them, so it is core, first-priority functionality alongside User
Story 1.

**Independent Test**: Can be fully tested by logging in, submitting a new
expense with a negative amount and no description, and confirming it is
saved with "refund" appended to its description and correctly reduces that
category's monthly total.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they submit a new expense with a
   negative amount and no description, **Then** the expense is saved with
   its description set to "refund".
2. **Given** a logged-in user, **When** they submit a new expense with a
   negative amount and a description that does not contain the word
   "refund", **Then** the expense is saved with "refund" appended to the
   description they entered.
3. **Given** a logged-in user, **When** they submit a new expense with a
   negative amount and a description that already contains "refund" in any
   letter case (for example "Refunded by store"), **Then** the description
   is saved exactly as entered, without appending the word a second time.
4. **Given** a logged-in user, **When** they submit a new expense with an
   amount of exactly zero, **Then** the system rejects the submission,
   unchanged from the existing rule that amounts must be non-zero.
5. **Given** a category with a negative (refund) expense recorded in the
   current month, **When** the user views that month's category totals and
   budget comparison, **Then** the refund amount is netted against that
   category's other expenses in the displayed total.

---

### User Story 3 - Edit a Previously Recorded Expense (Priority: P1)

A logged-in user changes the amount, category, date, or description of an
expense they recorded earlier in the current calendar month, so they can
correct a mistake (for example, the wrong category or a mistyped amount)
without needing to delete and re-enter it.

**Why this priority**: Correcting mistakes in already-recorded data is
explicitly requested and, alongside User Stories 1 and 2, completes the core
ask of this feature.

**Independent Test**: Can be fully tested by logging in as a user with an
existing expense recorded earlier in the current month, editing its amount,
and confirming the change is saved and reflected in that month's category
total and budget-vs-actual comparison.

**Acceptance Scenarios**:

1. **Given** a logged-in user with an expense recorded earlier in the
   current month, **When** they edit its amount, category, date, or
   description, **Then** the change is saved and that month's category
   totals and budget comparison reflect the updated value.
2. **Given** a logged-in user with an expense dated in a prior (closed)
   calendar month, **When** they attempt to edit it, **Then** the system
   rejects the edit and the expense remains exactly as originally recorded.
3. **Given** a logged-in user, **When** they submit an edit with an amount
   of exactly zero, a missing category, or a date outside the current
   calendar month, **Then** the system rejects the edit, explains what is
   invalid, and leaves the original expense unchanged.
4. **Given** two different user accounts, **When** one user attempts to edit
   the other user's expense (for example by guessing an identifier), **Then**
   the request is rejected and the other user's expense is unchanged.

---

### User Story 4 - Set Up a Recurring Expense (Priority: P2)

A logged-in user sets up a recurring expense once (for example, a monthly
rent payment or a weekly subscription), so that at the start of each month
they are prompted to confirm the expenses it produces instead of re-entering
them from scratch every time.

**Why this priority**: This is explicitly called out as an additional,
secondary capability in the request; it depends on nothing from User Stories
1-3 and delivers standalone value once they exist.

**Independent Test**: Can be fully tested by creating a recurring template
with an amount, category, and frequency, then, in a subsequent month,
confirming a pending occurrence and verifying the resulting expense appears
in the user's expense list and monthly totals like any other expense.

**Acceptance Scenarios**:

1. **Given** a logged-in user, **When** they create a recurring expense
   template with an amount, category, description, and frequency (weekly,
   monthly, or yearly), **Then** the template is saved as active.
2. **Given** an active recurring template and a new calendar month the user
   is visiting for the first time, **When** the template's frequency
   produces one or more due dates within that month, **Then** each due date
   appears as a separate pending occurrence for the user to review.
3. **Given** a pending occurrence, **When** the user confirms it as-is,
   **Then** an expense is created using the template's amount, category, and
   description, dated on the occurrence's due date, and the pending
   occurrence is removed from the list.
4. **Given** a pending occurrence, **When** the user adjusts its amount,
   category, description, or date and then adds it, **Then** an expense is
   created using the adjusted values instead of the template's original
   values, and the pending occurrence is removed from the list.
5. **Given** a pending occurrence, **When** the user skips it, **Then** no
   expense is created for that occurrence, and it is permanently removed
   from the list.
6. **Given** a logged-in user, **When** they view their expense list or
   monthly summary, **Then** expenses created from a confirmed or adjusted
   occurrence appear indistinguishably from manually entered expenses in
   totals and budget comparisons.

---

### User Story 5 - Manage an Existing Recurring Expense (Priority: P3)

A logged-in user changes the amount, category, or description of an active
recurring template, or cancels it entirely, so future pending occurrences
reflect the update (or stop appearing altogether) without altering expenses
already confirmed.

**Why this priority**: This depends on User Story 4 existing first and
refines it; it is not required for recurring expenses to deliver initial
value, so it is the lowest priority of the five.

**Independent Test**: Can be fully tested by editing an active recurring
template's amount and confirming a subsequent month's pending occurrence
reflects the new amount, then canceling the template and confirming no
further pending occurrences appear for it.

**Acceptance Scenarios**:

1. **Given** an active recurring template, **When** the user edits its
   amount, category, or description, **Then** any pending occurrence not yet
   confirmed or skipped reflects the updated values, while expenses already
   confirmed before the edit are unchanged.
2. **Given** an active recurring template with unconfirmed pending
   occurrences, **When** the user cancels it, **Then** those pending
   occurrences are removed and no further occurrences are ever produced for
   it, while expenses already confirmed remain in the user's history
   unchanged.

---

### Edge Cases

- A user attempts to edit an expense dated in a prior (closed) calendar
  month: the edit is rejected, protecting that month's historical totals and
  budget comparison from being altered after the fact.
- A user submits a negative amount without the word "refund" anywhere in the
  description: the system appends the word "refund" automatically rather
  than rejecting the submission.
- A user submits a negative amount with a description that already contains
  "refund" in any letter case: the system does not append the word a second
  time.
- A recurring template's frequency produces a due date that does not exist
  in a given month (for example, the 31st in a 30-day month): that
  occurrence's due date resolves to the month's last valid day instead.
- A recurring template with a weekly frequency produces more than one due
  date within the same calendar month: each due date appears as its own,
  separately confirmable/skippable pending occurrence.
- A user does not visit the app at all during a given calendar month: that
  month's occurrences are never presented and are not carried forward as a
  backlog into a later month.
- A recurring template is created partway through the current calendar month
  (for example, on the 15th, for a template whose monthly due date is the
  1st): it still produces a pending occurrence for that already-passed due
  date within the current month, since the current-month window runs from
  the 1st through today regardless of when the template was created.
- A user cancels a recurring template while it still has unconfirmed pending
  occurrences for the current month: those pending occurrences are removed
  and will not be offered again; expenses already confirmed earlier in the
  month are unaffected.
- An expense created from a confirmed or adjusted recurring occurrence is
  treated as an ordinary expense afterward: it can be edited like any other
  expense recorded in the current month (User Story 3), and doing so has no
  effect on its originating template or other occurrences.
- Two requests are processed on either side of a calendar month boundary
  (for example, one just before and one just after midnight UTC on the
  1st): each request's "current calendar month" is determined independently
  by its own processing time (FR-001), so they may correctly be evaluated
  against different months rather than needing to agree on a single answer.
- A user adjusts a pending occurrence to a date outside the current calendar
  month, a future date, or a zero amount: the adjustment is rejected with an
  explanation, and the occurrence remains pending, not confirmed or skipped,
  so the user can correct and retry.
- A user attempts to create a recurring template with a zero or negative
  amount: the submission is rejected, since recurring templates only
  support positive amounts (FR-010a).
- A user creates a second recurring template with the same amount,
  category, and frequency as an existing one: both are allowed to coexist;
  there is no deduplication or warning, since a user may genuinely have two
  independent recurring expenses that happen to match.
- A pending occurrence's adjust form was already open when its template got
  edited (FR-014): submitting it afterward is unaffected, since the
  adjust-and-add path validates only the values actually submitted (FR-012),
  not the template's current values; the user simply doesn't see the
  template's newer defaults unless they reload the form first.
- Two requests attempt to confirm, adjust-and-add, or skip the same
  (template, due-date) pair at the same time: the database's uniqueness
  constraint on that pairing (data-model.md § RecurringOccurrenceAction)
  ensures only the first succeeds; the second is rejected the same way a
  request for an already-actioned occurrence is.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a logged-in user to record a new expense
  dated any day from the first day of the current calendar month through
  today, inclusive, and MUST reject a date in a prior calendar month. The
  current calendar month is the calendar month containing the server's UTC
  calendar day at the time of the request, the same time basis as spec
  001 FR-007's definition of "today," evaluated fresh on each request
  rather than cached; every other requirement in this feature that
  references "the current calendar month" uses this same definition.
- **FR-002**: System MUST continue to reject an expense submission dated in
  the future, unchanged from the existing rule.
- **FR-003**: System MUST allow an expense's amount to be negative, in
  addition to positive, to represent a refund or credit; an amount of
  exactly zero remains invalid and MUST be rejected.
- **FR-004**: System MUST ensure that whenever an expense's amount is
  negative, its description contains the word "refund" (case-insensitive
  match); if the submitted description does not already contain that word,
  System MUST append it automatically rather than rejecting the submission.
- **FR-005**: System MUST allow a logged-in user to edit the amount,
  category, date, and description of a previously recorded expense that
  belongs to them, provided that expense's date falls within the current
  calendar month.
- **FR-006**: System MUST reject an attempt to edit an expense dated in a
  prior (closed) calendar month, leaving it unchanged.
- **FR-007**: System MUST validate an edited expense using the same rules as
  a newly created expense (FR-001 through FR-004): a non-zero amount
  truncated to 2 decimal places (with the refund description rule applied
  when negative), a category from the fixed set, and a date within the
  current calendar month.
- **FR-008**: System MUST NOT allow a user to view or edit another user's
  expense.
- **FR-009**: System MUST reflect an edited or newly added expense in the
  current month's category totals and budget-vs-actual comparison
  immediately after the change.
- **FR-010**: System MUST allow a logged-in user to create a recurring
  expense template specifying an amount, category, description, and a
  frequency (weekly, monthly, or yearly).
- **FR-010a**: A recurring expense template's amount MUST be positive;
  System MUST reject a zero or negative template amount. Recurring refunds
  are not supported; a refund is always recorded as an ad hoc negative-
  amount expense (FR-003), including via the adjust-and-add path on a
  pending occurrence (FR-012).
- **FR-010b**: System MUST display, for each active recurring template,
  its computed recurrence pattern (e.g., "recurs on the 15th of each
  month," "recurs weekly on Wednesdays," "recurs yearly on March 3"),
  derived from its creation date and frequency (FR-011a), so the user
  knows its schedule without waiting for a pending occurrence to appear.
- **FR-011**: System MUST NOT generate a recurring template's occurrences
  automatically in the background. Instead, on each request to `/recurring`
  or one of its occurrence-action routes (confirm, adjust, skip), System
  MUST present, for every active recurring template, one pending occurrence
  for each due date that template's frequency produces within the current
  calendar month up to and including today. This computation is scoped to
  those routes only; it is not a cross-cutting check on every authenticated
  request, and no other page (for example `/expenses`) surfaces pending
  occurrences. This computation is stateless
  with respect to past months: System MUST NOT backfill or otherwise present
  pending occurrences for any calendar month other than the current one,
  regardless of when the user last visited or when the template was created.
- **FR-011a**: A template's due dates are anchored to its creation date: its
  first occurrence is the creation date itself, and each subsequent
  occurrence is one frequency interval later (7 days for weekly; the same
  day-of-month for monthly, resolved per FR-018 when that day doesn't exist;
  the same month-and-day for yearly).
- **FR-012**: For each pending occurrence, System MUST allow the user to:
  (a) confirm it as-is, creating an expense with the template's amount,
  category, and description dated on the occurrence's due date; (b) adjust
  its amount, category, description, and/or date and then add it, creating
  an expense with the adjusted values instead; or (c) skip it, dismissing it
  permanently without creating an expense. An expense created via (a) or (b)
  MUST pass the same validation as any other expense (FR-001 through
  FR-004): its date MUST fall within the current calendar month and MUST
  NOT be in the future, and its amount MUST be non-zero, truncated to 2
  decimal places, with the refund-description rule applied when negative.
  An adjustment that fails this validation MUST be rejected, explained to
  the user, and MUST leave the pending occurrence in place (not confirmed,
  not skipped) so the user can correct and retry.
- **FR-013**: Once a pending occurrence is confirmed, adjusted-and-added, or
  skipped, System MUST remove it from that month's pending list; that
  action is final for that occurrence (no undo). A later month's occurrence
  produced by the same template is a separate, independent item and MUST
  still be offered normally on its own schedule; this requirement governs
  one occurrence at a time and has no bearing on whether the template keeps
  producing future occurrences at all, which canceling it (FR-015) controls.
- **FR-014**: System MUST allow a logged-in user to edit an active recurring
  template's amount, category, or description; any pending occurrence not
  yet confirmed or skipped MUST reflect the updated values, while an expense
  already confirmed before the edit MUST remain unchanged.
- **FR-014a**: System MUST NOT allow a recurring template's frequency to be
  changed after creation; a user who wants a different frequency must cancel
  the template (FR-015) and create a new one.
- **FR-015**: System MUST allow a logged-in user to cancel an active
  recurring template, after which System MUST remove any of its unconfirmed
  pending occurrences and MUST NOT produce further occurrences for it.
- **FR-015a**: System MUST NOT allow a canceled recurring template to be
  reactivated; a user who wants to resume it MUST create a new template.
- **FR-015b**: A canceled recurring template MUST NOT be displayed on
  `/recurring`; no historical or canceled-templates view is provided. Its
  previously confirmed expenses remain in the user's expense history
  regardless (FR-015).
- **FR-016**: System MUST NOT show a user another user's recurring templates
  or the pending occurrences or expenses they produce.
- **FR-017**: An expense created from a confirmed or adjusted recurring
  occurrence MUST be counted identically to a manually entered expense in
  monthly category totals and budget-vs-actual comparison. In the expense
  list, it MUST carry a small visual indicator marking its recurring origin
  (FR-017a); this indicator has no effect on any total or comparison.
- **FR-017a**: System MUST be able to determine, for any expense, whether it
  originated from a confirmed or adjusted recurring occurrence (via its
  linked `RecurringOccurrenceAction`, data-model.md), in order to render the
  indicator required by FR-017.
- **FR-018**: System MUST resolve a recurring occurrence due date that does
  not exist in a given month (for example, the 31st in a 30-day month) to
  that month's last valid day.

### Key Entities

- **Expense** (extended): Now editable after creation, but only while its
  date remains within the current calendar month; once the month closes, it
  is read-only. Its amount may be negative to represent a refund, in which
  case its description is guaranteed to contain the word "refund". May
  optionally reference the recurring occurrence that produced it.
- **Recurring Expense Template**: A user-owned definition of a repeating
  expense, consisting of a positive amount (negative/refund templates are
  not supported), a category (from the same fixed set as expenses), an
  optional description, a frequency (weekly, monthly, or yearly, fixed at
  creation and never editable), and a status (active or canceled). Produces
  Recurring Occurrences rather than expenses directly.
- **Recurring Occurrence**: A single due date produced by a Recurring
  Expense Template's frequency within the current calendar month. It is
  "pending" only in the sense that no decision has been recorded for it yet
  (this is a computed state, not a stored one); once the user confirms,
  adjusts-and-adds, or skips it, that decision is recorded permanently as
  either confirmed (referencing the Expense it produced) or skipped. Not
  itself a financial record until confirmed.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can record a refund as a negative-amount expense and
  see it correctly net against that category's monthly total, with no
  discrepancy between the recorded amounts and the displayed total.
- **SC-002**: A user can add a forgotten expense for an earlier date in the
  current month and have it counted correctly in that month's totals, with
  no discrepancy.
- **SC-003**: A user can correct a mistake in an expense recorded earlier in
  the current month and see the correction reflected in that month's
  category total and budget comparison, with no discrepancy.
- **SC-004**: 100% of attempts to edit an expense dated in a prior calendar
  month are rejected, and 100% of attempts by one account to view or edit
  another account's expense or recurring template are rejected.
- **SC-005**: A user can set up a recurring expense once and, across the
  next 3 calendar months, be offered a pending occurrence to confirm, adjust,
  or skip in each of those months without re-creating the template. Verified
  without waiting 3 real months: a test computes the occurrence-generation
  logic directly against 3 successive simulated "current months," the same
  way spec 001's tests simulate a fixed "today" rather than waiting on the
  real clock.
- **SC-006**: 100% of expenses attributed to a recurring template exist only
  because the user took an explicit action (confirm or adjust-and-add) on
  their corresponding pending occurrence; the system never creates such an
  expense on its own, verified automatically by tests asserting no expense
  exists for an occurrence until that action is taken.
- **SC-007**: Every new route this feature adds (editing an expense,
  creating/canceling a recurring template, confirming/adjusting/skipping a
  pending occurrence) responds within the 200ms per-request server-side
  latency budget established in spec 001's Clarifications, verified
  automatically the same way (per-request latency assertions).

## Assumptions

- Editing an expense does not keep a history of its prior values in this
  increment; only the current values are stored, consistent with this
  project's existing scope decisions for the MVP.
- A recurring template offers exactly three frequency options: weekly,
  monthly, and yearly. Custom/arbitrary intervals are out of scope.
- There is no cross-check between a negative (refund) expense and any
  specific original expense it may be refunding; it is recorded as an
  independent entry netted purely through category/month summation.
- Recurring templates, their pending occurrences, and the expenses they
  produce are private to the owning user, following the same isolation rule
  already established for expenses and budgets.
- This feature does not change the existing fixed category list (Food,
  Transportation, Housing, Utilities, Entertainment, Health, Other); expenses
  (including refunds) and recurring templates all use the same set.
- Deleting an expense outright remains out of scope for this feature, as it
  did for the MVP; refunds are represented via a negative-amount entry
  instead (User Story 2).
- Because both new and edited expense dates are confined to the current
  calendar month, a prior (closed) month's totals and budget comparison are
  never altered by this feature.
- A canceled recurring template cannot be reactivated; a user who wants the
  same recurring expense again creates a new template.
- This feature's new routes are expected to meet the same 200ms per-request
  server-side latency budget established in spec 001, since none of them
  perform password hashing or other inherently expensive work.
- A recurring template's amount is always positive; there is no such thing
  as a recurring refund in this feature. A refund arising from a recurring
  expense (for example, a refunded subscription charge) is instead recorded
  as its own ad hoc negative-amount expense (User Story 2), independent of
  the template.
- No maximum number of active recurring templates per user is imposed; this
  is unbounded, consistent with the low-tens-per-user scale already assumed
  in plan.md § Scale/Scope.
- No success criterion measures the recurring feature's time-saved value
  versus manual re-entry, since that kind of qualitative UX metric isn't
  code-testable, the same reasoning that replaced the original SC-006 with
  a testable system-behavior invariant instead. SC-005 and SC-006 measure
  correctness and the confirm-before-creation guarantee; measuring
  perceived value is left to qualitative user research, out of scope here.
