# ResourceHub — Project Brief

## What

ResourceHub is a Windows desktop batch file rename tool built with Python 3.12+ and PySide6.

## Why

To provide a safe, previewable, rule-based batch rename experience with full Unicode support and undo capability.

## Current Version

**M15 RC** (Release Candidate)

## Completed Capabilities

- **Scanner**: Non-recursive directory scan via `os.scandir()`
- **Rule Engine**: 10 RuleStep types (replace, remove_text, regex_replace, case, trim, number, insert, date, add_prefix, add_suffix)
- **Preview Engine**: Real-time preview with context (index, metadata via MetadataProvider)
- **RenamePlan Engine**: Unified plan generation + conflict detection + legality checks
- **Rename Engine**: Policy-based execution (FAIL/SKIP/OVERWRITE)
- **Undo Engine**: Single-level undo via OperationLogger
- **Rule Manager**: Full CRUD + RuleStep editor with type selection, parameter editing, ordering
- **Settings**: QSettings-based RenamePolicy persistence
- **i18n**: zh_CN / en_US via Qt Linguist .ts files
- **Packaging**: PyInstaller build with translations

## Current Stage

Release Candidate validation. Feature freeze on all core modules.

## Next Stage

M16 Planning.
