# Specification Quality Checklist: Retroactive Expense Editing and Recurring Transactions

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-09-07
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`
- All 3 [NEEDS CLARIFICATION] markers were resolved interactively during
  `/speckit-specify` and recorded under `## Clarifications` in spec.md:
  backdating/editing is confined to the current calendar month; refunds are
  a new negative-amount expense (not deletion or in-place editing), with
  "refund" auto-appended to the description when missing; and recurring
  occurrences are user-confirmed (not auto-generated), surfaced as a pending
  list once per calendar month.
- The resolved answers materially reshaped the feature: what began as a
  single "edit an expense" story split into three (backdate, refund, edit),
  and recurring transactions gained a new Recurring Occurrence entity to
  track pending/confirmed/skipped state.
- A `/speckit-clarify` pass (same day) resolved 3 more scope-defining
  questions, recorded as further bullets under the same Clarifications
  session: pending-occurrence computation is stateless/current-month-only
  with no backfill; a recurring template's frequency is fixed at creation;
  and this feature's new routes inherit spec 001's 200ms latency budget.
- A subsequent manual review caught 4 further gaps, all fixed directly (also
  logged under the same Clarifications session): SC-006 was unmeasurable by
  an automated test (a user-comprehension metric) and was replaced with a
  testable system-behavior invariant; "current calendar month" was
  precisely defined in FR-001 (same UTC, per-request basis as spec 001's
  "today"); the adjust-and-add path was made to explicitly inherit the same
  date/amount/category validation as any other expense (FR-012), including
  what happens when that validation fails; and recurring templates were
  restricted to positive amounts only, with a "recurring refund" explicitly
  ruled out (FR-010a).
- Post-`/speckit-plan`, a question about FR-13's wording surfaced a
  miscommunication (not a behavior change): the data model already
  persisted actions per exact (template, due-date) pairing with no undo,
  correctly, but FR-013's "permanently, regardless of how many months pass"
  phrasing read as if it might affect the template's future recurrence
  rather than just that one occurrence. Reworded to say the removal is
  scoped to that month's list and final for that occurrence, with a
  distinct future occurrence being a separate, independent item, unrelated
  to stopping the template altogether (FR-015's job). No change to
  plan.md/data-model.md/research.md was needed.
- After `/speckit-tasks`, a dedicated `checklists/recurring-lifecycle.md`
  audit (17 items, the recurring-template/occurrence lifecycle specifically)
  found and resolved 7 real gaps via `/speckit-clarify`: the occurrence
  due-date anchor and first-occurrence timing (now FR-011a), which specific
  requests trigger pending-occurrence computation (FR-011, scoped to
  `/recurring`), whether users are told a template's recurrence pattern
  (FR-010b, new), whether canceled templates stay visible (FR-015b, no),
  and whether a recurring-sourced expense is visually distinguishable in
  the expense list (FR-017a, yes). The last one added new implementation
  scope (tasks T040a, T044a, T045a) and a new `contracts/web-routes.md` row
  for `GET /expenses`. 10 further items were resolved directly (consistency
  fixes, elevating assumptions to FRs, and documented decisions not to add
  scope) without needing a question. All 17 are now checked.
- Ready for `/speckit-plan`.
