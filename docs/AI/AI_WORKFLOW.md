# ResourceHub — AI Collaboration Workflow

## Roles

### Reviewer (ChatGPT / User)

- Architecture Review
- Milestone Planning
- Risk Assessment
- Acceptance Criteria
- Feature Freeze Decisions
- Design Approval

### Developer (OpenHands / AI Agent)

- Code Assessment (read-only analysis before implementation)
- Implementation (code + tests)
- Automated Testing (pytest)
- Documentation (AGENTS.md, docs/AI/)
- Git Tag + Commit

## Standard Milestone Flow

```
Assessment (design doc, no code)
    ↓ Approval
Implementation (code + tests)
    ↓ pytest all pass
Validation (behavior verification)
    ↓
Smoke Test (real directory)
    ↓
Git Tag (Mxx-complete)
    ↓
Feature Freeze
    ↓
Update docs/AI/
    ↓
Next Milestone
```

## Rules for AI Developer

- Don't modify frozen modules without explicit approval
- Don't expand scope beyond the user's request
- Don't speculate — use code, tests, and real output as evidence
- Read `docs/AI/` on session start for context
