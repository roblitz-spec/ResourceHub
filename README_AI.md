# ResourceHub — AI Onboarding

> If you are an AI agent entering this project for the first time,
> read these files in order before making any changes.

## Required Reading Order

1. [`docs/AI/PROJECT_BRIEF.md`](docs/AI/PROJECT_BRIEF.md) — What, why, current version
2. [`docs/AI/CURRENT_STATUS.md`](docs/AI/CURRENT_STATUS.md) — Freeze state, tests, tags
3. [`docs/AI/AI_HANDOFF.md`](docs/AI/AI_HANDOFF.md) — Quick context restore
4. [`docs/AI/ARCHITECTURE.md`](docs/AI/ARCHITECTURE.md) — Pipeline, module boundaries, hard rules
5. [`docs/AI/DEVELOPMENT_CONSTITUTION.md`](docs/AI/DEVELOPMENT_CONSTITUTION.md) — Principles you must follow
6. [`docs/AI/AI_WORKFLOW.md`](docs/AI/AI_WORKFLOW.md) — How Reviewer + Developer collaborate
7. [`docs/AI/TEST_STRATEGY.md`](docs/AI/TEST_STRATEGY.md) — Test layers and release gates
8. [`docs/AI/NEXT_MILESTONE.md`](docs/AI/NEXT_MILESTONE.md) — Upcoming work

## Quick Commands

```bash
# Run all tests
python -m pytest tests/ -q

# Run with profiling
RESOURCEHUB_DEBUG=1 python main.py

# Build
python scripts/build.py
```
