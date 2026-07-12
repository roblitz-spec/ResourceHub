# ResourceHub — Current Status

**Version**: M15 RC
**Date**: 2026-07-11

## Test Status

| Metric | Value |
|---|---|
| Automated Tests | **152 PASS** |
| Regression Matrix | **PASS** (32 scenarios) |
| Unit + Integration | PASS |
| Preview==Rename E2E | PASS |
| Undo Cycle | PASS |
| Boundary (Unicode/Long/Conflict) | PASS |

## Blocker

**None.**

## Manual QA

PASS — Smoke tests cover: scan, preview, rename, undo, rule persistence.

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
