# ResourceHub — Known Limitations

> Update this file when a limitation is resolved.

## Undo

- **Single Level Only**: Only the most recent rename session can be undone. No multi-level undo stack.
- **No Redo**: Undo cannot be reversed.

## Prefix / Suffix

- **Independent Rules**: `add_prefix` and `add_suffix` are separate RuleStep types. No unified "Insert at position" rule for prefix+suffix.
- **No Position Parameter**: Cannot switch a prefix rule to suffix without deleting and re-creating.

## Performance

- **5000+ Files**: Not formally benchmarked. Scanner uses `os.scandir()` which is efficient, but QTableView rendering with 5000+ rows is untested.
- **NAS/SMB**: Optimized via `os.scandir()` (cached attributes), but no formal SMB latency benchmark.

## Directory Rename

- **Directory + File Unified Pipeline**: Directories and files share the same Rename Pipeline (Preview → RenamePlan → Rename → Undo).
- **No Recursive Rename**: Directory rename does not affect directory contents. Only the directory name itself is changed.

## Rule Extensibility

- **No User Scripts**: RuleStep types are hardcoded in `_HANDLERS`. Users cannot add custom Python scripts.
- **No Plugin System**: All Rule types must be compiled into the application.

## UI

- **No Drag-and-Drop**: Step reordering uses ↑↓ buttons only.
- **No Dark Mode**: UI uses system default theme.

## Selection & Input

- ✅ **Multi File Selection**: Supported (Ctrl+Click / Shift+Click in table).
- ✅ **Multi Directory Selection**: Supported.
- ✅ **File + Directory Mixed Selection**: Supported.
- ✅ **Batch Rename + Undo**: Supported.

The following are **design decisions** (not bugs) — future optional enhancements:

- **No Drag-and-Drop Resource Input**: Resources are added via directory browse, not drag-and-drop.
- **No Add Resources**: Cannot append additional resources to an existing scan result (requires re-scan).
- **No Workspace / Favorites**: No persistent workspace or favorite-directory management.

## Serialization

- **JSON Only**: Rule configuration is stored as JSON. No migration versioning beyond the `version: 1` field.
- **No Export/Import for Rules**: Rules can't be shared as standalone files.
