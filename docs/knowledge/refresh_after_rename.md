# Refresh Strategy After Rename

## Original Implementation (Removed)

```
Rename → Path.rename()
       → Mutate existing FileItem objects in-place
         (item.full_path = plan.target,
          item.original_name = plan.target_name,
          item.base_name = plan.target.stem)
       → FileTableModel.refresh_all()
```

### Problems

1. **Stale in-memory state.** After mutation, `FileItem` no longer represents the filesystem. `full_path` points to the new location, but the object identity is blurred between "old file" and "new file."

2. **Incorrect preview generation.** Subsequent `_refresh_preview()` operates on mutated items where `base_name` and `original_name` already reflect the post-rename state. A new rule applied after rename sees the renamed name, not the original.

3. **False duplicate detection.** When `full_path` is mutated to the target and a second rename is attempted on the same items, `plan.target == plan.source` can trigger incorrectly because the source is already the target.

4. **Inconsistent behavior with Undo.** Undo uses `_start_scan()` (full rescan), but Rename used in-place mutation — different refresh strategies for the same class of operation.

## Final Implementation

```
Rename → Path.rename()
       → _start_scan(directory)       ← full rescan
         → Scanner.scan()
         → PreviewEngine.generate_preview()
         → FileTableModel.set_items()
```

Same strategy as Undo. Filesystem is the single source of truth.

## Design Principle

**FileItem represents a filesystem snapshot, not mutable business state.**

After any filesystem mutation (rename, undo), the cached FileItem collection is stale. Rather than attempting to keep it in sync through mutation, discard and rebuild from the filesystem.

A rescan is O(n) directory enumeration — the same cost as the initial scan. On SMB/NAS, `os.scandir()` is a single network request. The cost is negligible compared to the correctness guarantee.

## See Also

- [windows_case_only_rename.md](windows_case_only_rename.md) — Windows case-only rename investigation
- [../development/current_status.md](../development/current_status.md) — Current project status
