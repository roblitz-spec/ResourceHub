# ResourceHub — AI Onboarding & Memory Governance

**AI Memory Version**: v1.0

## Purpose

`docs/AI/` is the long-term memory for AI collaborators. It enables:
- New ChatGPT/OpenHands sessions to restore project context in minutes
- Consistent development across Milestones without relying on chat history
- Clear governance of what gets updated and when

## Required Reading Order

| # | Document | Purpose |
|---|---|---|
| 1 | `PROJECT_BRIEF.md` | What, why, current version |
| 2 | `CURRENT_STATUS.md` | Freeze state, test counts, Git tags |
| 3 | `AI_HANDOFF.md` | Quick context restore for new sessions |
| 4 | `ARCHITECTURE.md` | Pipeline diagram, module boundaries, hard rules |
| 5 | `DEVELOPMENT_CONSTITUTION.md` | 10 principles; when they can be broken |
| 6 | `AI_WORKFLOW.md` | Reviewer ↔ Developer collaboration flow |
| 7 | `TEST_STRATEGY.md` | Test layers; what is release-blocking |
| 8 | `DECISION_LOG.md` | Historical ADRs (architecture decisions only) |
| 9 | `KNOWN_LIMITATIONS.md` | Current constraints; update when resolved |
| 10 | `NEXT_MILESTONE.md` | Candidate features for next Milestone |
| 11 | `CHANGELOG_AI.md` | Per-Milestone timeline |
| 12 | `REVIEW_GUIDELINES.md` | Reviewer checklist |

## Documentation Lifecycle

| Document | Update Trigger |
|---|---|
| `PROJECT_BRIEF.md` | Major release (Mxx.0) |
| `CURRENT_STATUS.md` | **Every Milestone** |
| `AI_HANDOFF.md` | **Every Milestone** |
| `CHANGELOG_AI.md` | **Every Milestone** |
| `NEXT_MILESTONE.md` | **Every Milestone** (plan next) |
| `DECISION_LOG.md` | Architecture decision only (ADR) |
| `KNOWN_LIMITATIONS.md` | When a limitation changes |
| `ARCHITECTURE.md` | When pipeline or boundaries change |
| `TEST_STRATEGY.md` | When test policy changes |
| `DEVELOPMENT_CONSTITUTION.md` | Rarely — only for principle changes |
| `AI_WORKFLOW.md` | Rarely |
| `REVIEW_GUIDELINES.md` | Rarely |

## Mandatory Update Checklist (Every Milestone)

```
□ CURRENT_STATUS.md    — version, test count, freeze state
□ CHANGELOG_AI.md      — new Milestone entry
□ NEXT_MILESTONE.md    — plan next
□ AI_HANDOFF.md        — current state snapshot

If architecture changed:
□ DECISION_LOG.md      — new ADR

If test policy changed:
□ TEST_STRATEGY.md
```

## Release Exit Criteria

A Milestone is complete only when:

```
✓ pytest all pass
✓ Regression matrix pass
✓ Documentation updated (checklist above)
✓ AI Memory updated
✓ Git tag created (Mxx-complete)
✓ Feature Freeze declared
✓ Reviewer approved
```

## Quick Commands

```bash
python -m pytest tests/ -q          # All tests
RESOURCEHUB_DEBUG=1 python main.py  # With profiling
python scripts/build.py             # Package
```
