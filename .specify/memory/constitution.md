<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles:
  - II. Real Database, No Shortcuts: expanded to require automated tests run
    via a dedicated, non-production test service/image rather than the app's
    production build target
  - V. Docker Is the Source of Truth: expanded to require multi-stage builds
    that keep the production image lean (no build toolchain, dev
    dependencies, or test files), a non-root container user, and lockfile-
    pinned dependencies
- Added principles: none (existing principles expanded; see above)
- Added sections: none
- Removed sections: none
- Templates requiring follow-up: none. No dependent templates reference
  specific principle names or counts that would break with this expansion.
- Deferred placeholders: none
- Rationale for MINOR bump: both changes materially expand existing
  principles with new non-negotiable MUST rules (multi-stage/lean images,
  non-root containers, lockfile pinning, isolated test execution) that
  codify practices already implemented in this repo (multi-stage Dockerfile,
  non-root user, uv.lock adoption, profile-gated test service) but were not
  previously governed by any principle. No principle was removed or
  redefined, so this is not a MAJOR change.
-->

# Expense Tracker Constitution

## Core Principles

### I. Test-First Development
Every new endpoint MUST have a failing test committed before its implementation
code. No PR merges with untested routes. This ordering (test, confirm red,
implement, confirm green) is the only accepted way to add or change route
behavior; retrofitting tests after the implementation commit does not satisfy
this principle.

### II. Real Database, No Shortcuts
Development and tests MUST run against PostgreSQL via Docker Compose. SQLite,
in-memory databases, and mocked DB calls MUST NOT be used as a substitute in
any environment. Tests that pass against a stand-in database but not the real
one hide bugs that only surface in production; running everything against the
same PostgreSQL engine used in production eliminates that class of failure.

Automated tests MUST run via a dedicated, non-production service/image (a
`test` build target or equivalent), never against the app's production build
target. This keeps dev/test tooling out of the deployed image (Principle V)
while still exercising the same real PostgreSQL engine the app uses in
production, so a passing test run is never an artifact of a different runtime
than what ships.

### III. Migrations Are the Only Schema Change Path
All schema changes MUST go through an Alembic migration. SQLAlchemy's
auto-create MUST NOT be relied upon, and manual `ALTER TABLE` statements
against the dev database MUST NOT be used. Every schema change must be
reviewable, reversible, and reproducible across environments, which only a
committed migration script guarantees.

### IV. Async All the Way Down
Request handlers MUST use SQLAlchemy's async session; no sync DB calls are
permitted inside a request handler. A single sync call inside an async handler
blocks the event loop for every concurrent request, so the async boundary
MUST be preserved end-to-end from the handler down to the database driver.

### V. Docker Is the Source of Truth
The app MUST run via `docker compose up --build` with no host dependencies
beyond Docker itself. Any setup step that only works because of a locally
installed interpreter, library, or service outside the Compose stack is a
violation, because it breaks reproducibility for every other contributor and
for CI.

Production images MUST be built via a multi-stage Dockerfile whose final
runtime stage excludes build toolchains (compilers, dev headers), development
dependencies, and test files. A lean runtime image reduces attack surface and
guarantees that what is tested for reproducibility is the same artifact that
ships, not a superset of it.

Containers MUST run as a non-root user. Running the application process as
root inside the container is not permitted, since a container compromise
under root grants unnecessary host-adjacent privilege.

Dependency versions MUST be pinned via a committed lockfile (currently
`uv.lock`). Floating version ranges in `pyproject.toml` alone MUST NOT be
relied upon for reproducible builds, since an unpinned resolution can silently
change between builds and break the guarantee that Docker is the source of
truth for what runs.

### VI. Secrets Never Committed
Database credentials and the JWT signing key MUST come from environment
variables loaded via `.env`, and `.env` MUST stay in `.gitignore`. No
credential or signing key may be hardcoded in source, committed in a config
file, or checked in under any filename that bypasses `.gitignore`.

## Technology Stack Constraints

The backend persistence layer is PostgreSQL, accessed exclusively through
SQLAlchemy's async engine/session and evolved exclusively through Alembic
migrations (Principles II, III, IV). Authentication relies on a JWT signing
key supplied via environment variables (Principle VI). The full application,
including its database, MUST be launchable through Docker Compose with no
additional host setup (Principle V). Production images MUST be multi-stage,
lean, non-root, and built from lockfile-pinned dependencies; automated tests
MUST run via a separate non-production service/image against the same real
PostgreSQL engine (Principles II, V). Any proposal to introduce a different
database engine, a sync ORM/session path, a host-only dependency, a root-run
container, or an unpinned/floating dependency resolution requires a
constitution amendment before implementation.

## Development Workflow

Every PR that adds or changes a route MUST show a test commit that predates
the implementation commit and MUST demonstrate the test failed before the
implementation and passes after (Principle I). PRs that add or change schema
MUST include an Alembic migration in the same PR: no schema diff is
reviewable without one (Principle III). Reviewers MUST reject any handler
code containing a sync DB call (Principle IV) and any diff that adds a
credential, key, or `.env` file to version control (Principle VI). Reviewers
MUST also reject any change that adds a build toolchain, dev dependency, or
test file to a production image's final stage, runs a container process as
root, or removes/relaxes lockfile pinning in favor of floating dependency
ranges (Principle V), and any change that points the test suite at the app's
production build target instead of the dedicated test service/image
(Principle II). CI and local development MUST both exercise the app through
`docker compose up --build` against real PostgreSQL (Principles II, V); a
green run against any other database or a locally-run interpreter does not
satisfy a merge gate.

## Governance

This constitution supersedes any conflicting practice, script, or prior
convention in this repository. Amendments require: (1) a documented rationale
for the change, (2) an update to this file following the same drafting rules
used to create it, and (3) a version bump per the policy below. Use
`speckit-constitution` to make amendments. Do not hand-edit this file.

Versioning policy (semantic versioning applied to governance):
- MAJOR: Backward-incompatible governance changes, including removing or
  redefining an existing principle.
- MINOR: Adding a new principle or materially expanding an existing one.
- PATCH: Wording clarifications and non-semantic refinements.

All PRs and code reviews MUST verify compliance with the Core Principles
above; any deviation must be justified in the PR description and approved
before merge, or the constitution must be amended first. Complexity or
deviation that cannot be justified against these principles MUST be
simplified or rejected.

**Version**: 1.1.0 | **Ratified**: 2026-08-27 | **Last Amended**: 2026-09-07
