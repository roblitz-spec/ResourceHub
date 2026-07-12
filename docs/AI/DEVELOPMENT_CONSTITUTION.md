# ResourceHub — Development Constitution

## Core Principles

1. **Stability First** — Release quality matters more than feature count
2. **Compatibility First** — Existing `rules.json` must load without error
3. **Extension over Modification** — New features add handlers, don't change existing ones
4. **Feature Freeze is Hard** — Once a Milestone closes, only Bug Fixes are allowed
5. **Rule Single Responsibility** — Each RuleStep type does one transformation
6. **Tests Required** — Every behavioral change must have a test
7. **Assessment Required** — Architecture, Pipeline, or Serialization changes need prior design review
8. **Manual QA Required** — Automated tests are not sufficient for release
9. **AI Stays in Scope** — Don't expand the task beyond the user's explicit request
10. **Documents are Source of Truth** — `docs/AI/` is the long-term memory for AI collaborators

## When Rules Can Be Broken

- Major version bump (M→N where N ≥ next major)
- Explicit user directive to refactor a frozen module
- Security vulnerability requiring immediate fix
