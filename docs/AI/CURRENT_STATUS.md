# ResourceHub — Current Status

**Version**: M11.1
**Date**: 2026-07-15

## Test Status

| Metric | Value |
|---|---|
| Automated Tests | **176 PASS** |
| Regression Matrix | **PASS** |
| Unit + Integration | PASS |
| Preview==Rename E2E | PASS |
| Undo Cycle | PASS |
| Boundary (Unicode/Long/Conflict) | PASS |
| Multi-Select (File+Dir+Mixed) | PASS |

## Blocker

**None.**

## Project Status

| Item | Status |
|---|---|
| Architecture | Stable |
| Rename Pipeline | Stable |
| Rule Dependency Analysis | Stable |
| Scanner API | Stable (`scan(paths: list[Path])`) |
| Multi File Selection | Supported |
| Multi Directory Selection | Supported |
| Mixed Selection | Supported |
| Batch Rename | Supported |
| Batch Undo | Supported |

## Manual QA

PASS — Smoke tests cover: scan, preview, rename (batch), undo, rule persistence.

## Feature Freeze

The following modules are frozen. Changes require explicit approval:

| Module | Reason | When Unfrozen |
|---|---|---|
| `engine/rule_engine.py` | 10 Rule types stable, pure-function contract | Major version bump |
| `engine/rename_engine.py` | Plan-based execution stable | Architecture change |
| `engine/preview_engine.py` | Context contract frozen | New context field needed |
| `engine/rename_plan_engine.py` | Conflict detection stable | New conflict type |
| `ui/file_table_model.py` | `dataChanged` refresh stable | Performance regression |

## Git Tags

| Tag | Content |
|---|---|
| `M12-complete` | Number Rule |
| `M13-complete` | Insert Rule |
| `M14-complete` | Date Rule |
| `M15-complete` | AddSuffix Rule |
| `M16-complete` | AI Memory v2.0 Governance |
