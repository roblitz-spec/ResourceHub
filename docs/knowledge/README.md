# Knowledge Base

Engineering knowledge documents organized by topic. These complement the AI Memory system — read them when investigating a specific issue or making changes to a related module.

## Filesystem

### [windows_case_only_rename.md](windows_case_only_rename.md)
**Purpose**: Documents the Windows case-only rename bug, investigation process, and fix.
**When to read**: When working on rename conflict detection, Path comparisons, or Windows-specific filesystem behavior.
**Key lessons**:
- `Path.exists()` is case-insensitive on Windows — cannot distinguish case-only rename from genuine conflict
- Use `Path.samefile()` to compare filesystem identity (not path string)
- Filesystem APIs ≠ business semantics; verify platform-specific behavior on target OS
- Compare historical versions when debugging regressions

## Rename Workflow

### [refresh_after_rename.md](refresh_after_rename.md)
**Purpose**: Explains the rescan strategy after rename execution.
**When to read**: When modifying post-rename UI update logic or investigating stale preview issues.
**Key lessons**:
- FileItem is a filesystem snapshot, not mutable business state
- Rescan (full `_start_scan`) is preferred over in-place mutation after filesystem changes
- Same strategy used by both Rename and Undo
- `os.scandir()` is a single network request on SMB — rescan cost is negligible

## Preview Pipeline

*(placeholder — add documents as issues are investigated)*

## Architecture Decisions

*(see `docs/AI/DECISION_LOG.md` for formal ADRs)*

## Performance

*(placeholder — see Architecture docs for Network Filesystem Performance guidelines)*

## Platform Compatibility

### [windows_case_only_rename.md](windows_case_only_rename.md)
**See Filesystem section above.**

## Related

- `docs/AI/AI_MEMORY_PACK.md` — Default AI session entry point
- `docs/AI/ARCHITECTURE.md` — Pipeline diagram and module boundaries
- `docs/AI/DECISION_LOG.md` — Formal Architecture Decision Records
- `docs/development/current_status.md` — Current project status checkpoint
