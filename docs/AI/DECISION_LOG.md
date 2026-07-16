# ResourceHub — Decision Log (ADR)

## ADR-001: Prefix / Suffix Design

- **Milestone**: M15
- **Status**: Accepted
- **Decision**: Keep `add_prefix` and `add_suffix` as independent RuleStep types.
- **Reason**: Backward compatibility — existing `rules.json` with `add_prefix` must load without migration. Avoids modifying frozen Rule structure post Feature Freeze.
- **Alternatives Considered**: Unify into single Rule with `position` parameter. Rejected due to migration risk.

## ADR-002: Undo Design

- **Milestone**: M15
- **Status**: Accepted
- **Decision**: Maintain single-level Undo only.
- **Reason**: Satisfies current requirements. Multi-level Undo adds session management complexity (stack, redo, history UI) without proven user demand.
- **Alternatives Considered**: Multi-level Undo stack. Deferred to future Milestone.

## ADR-003: Feature Freeze Policy

- **Milestone**: M15 RC
- **Status**: Accepted
- **Decision**: Freeze core pipeline modules (RuleEngine, RenameEngine, PreviewEngine, RenamePlanEngine, FileTableModel) after M15 RC.
- **Reason**: Reduce regression risk. Prioritize release stability over continued iteration.
- **Alternatives Considered**: Allow continuous modification. Rejected — risk of destabilizing 152-test baseline.

## ADR-004: RuleEngine Pure Function Contract

- **Milestone**: M12 (Number Rule design)
- **Status**: Accepted
- **Decision**: RuleEngine handlers must be pure functions. State (like numbering index) is passed via `context` dict from PreviewEngine.
- **Reason**: Testability, predictability, thread safety. Avoids global counters that break between Preview and Rename cycles.
- **Alternatives Considered**: Module-level counters with `reset()`. Rejected — violates stateless principle.

## ADR-005: Context Contract

- **Milestone**: M14 (Date Rule)
- **Status**: Accepted
- **Decision**: Context fields (`index`, `metadata`) are frozen. `metadata` is a `MetadataProvider` with lazy `modified`/`created` properties. New fields can be added but existing ones cannot be renamed or re-typed.
- **Reason**: Rule handlers depend on these fields. Renaming breaks existing Rule configurations.

## ADR-006: Avoid Path.resolve() in Scanner Hot Path

- **Milestone**: M11.1 (NAS Performance Fix)
- **Status**: Accepted
- **Decision**: Scanner hot path must not call `Path.resolve()`, `realpath()`, or any per-entry filesystem stat. Use `Path(entry.path)` directly from `os.scandir()` results.
- **Context**: `os.scandir()` returns `DirEntry` objects with `.path` already being an absolute path. `Path.resolve()` calls `os.path.realpath()` which traverses every path component with `lstat()`. On network filesystems (SMB/NAS), each `lstat()` is one network round trip.
- **Problem**: Scanner on real SMB NAS with 605 directories took **252.524s**. Root cause: `Path(entry.path).resolve()` in `_scan_dir()` triggered 2,420 `lstat()` calls (605 entries × ~4 path components each).
- **Root Cause**: `resolve()` → `realpath()` → `lstat()` per path component → 2,420 network round trips on SMB.
- **Solution**: Remove `Path.resolve()`. Merge `is_dir()` + `is_file()` into single `stat()`. Use `DirEntry.is_dir()` (cached `d_type`).
- **Validation** (real SMB NAS):
  - Scanner: 252.524s → 0.494s (≈511×)
  - Rename: 201 directories ≈10s (normal)
  - Regression: 179 PASS
- **Trade-offs**: Without `resolve()`, symlinked paths are not resolved to their canonical form. The `seen` dedup set may not catch symlinked duplicates. This is acceptable because: (a) directories within a scan are not typically symlinked to each other; (b) the multi-path input case is the primary dedup scenario.
- **Lessons Learned**:
  1. Any directory scanning code must assume it may run on network filesystems.
  2. A single seemingly harmless filesystem API in a hot loop can cause 500× performance degradation.
  3. All future Scanner/Indexer/Rename/Metadata code reviews must include network filesystem performance as a default review item.
  4. Local SSD testing alone is insufficient — network filesystem latency must be considered in design.
- **Alternatives Considered**: Keep `resolve()` but add caching. Rejected — caching adds complexity; `os.scandir()` paths are already absolute.
