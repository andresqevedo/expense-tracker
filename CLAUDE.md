# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Constitution

This project's governing principles, constraints, and workflow rules live in
[`.specify/memory/constitution.md`](.specify/memory/constitution.md). Read it before
making non-trivial changes, and follow it as the source of truth whenever it
conflicts with general defaults. If the constitution itself needs to change, use
the `speckit-constitution` skill rather than editing it as a normal file.

## Spec-Driven Workflow

This repository uses the [Spec Kit](.specify/) workflow. Features are developed
through the following skills, generally in order:

1. `speckit-specify` — create/update a feature spec
2. `speckit-clarify` — resolve ambiguities in the spec
3. `speckit-plan` — produce the implementation plan
4. `speckit-tasks` — break the plan into ordered tasks
5. `speckit-analyze` — cross-check spec/plan/tasks for consistency
6. `speckit-implement` — execute the tasks
7. `speckit-converge` — reconcile the codebase against spec/plan/tasks

Feature artifacts are stored under `.specify/`.
