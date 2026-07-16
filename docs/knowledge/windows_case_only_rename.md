# Windows Case-Only Rename Detection

## 1. Background

ResourceHub supports batch file and directory renaming on Windows. On Windows, the NTFS filesystem is case-insensitive by default: `NO.TEST001.txt` and `No.TEST001.txt` refer to the same file.

A user reported that after applying a simple case-changing rule (`NO.` → `No.`), the preview correctly showed `No.TEST001.txt`, but clicking "Rename" produced:

> 目标文件已存在 (Target file already exists)

The rename was blocked despite no other file with that name existing in the directory.

## 2. Investigation Timeline

| Step | Action | Finding | Scope Narrowed |
|---|---|---|---|
| 1 | Verify Preview output | `preview_name=No.TEST001` — correct | PreviewEngine is not the issue |
| 2 | Trace Preview → RenamePlan data flow | `preview_name` preserved in `RenamePlanEngine.generate()` | Data transfer is correct |
| 3 | Check `needs_rename` | `True` — correctly identifies name change | Step 1 logic is correct |
| 4 | Trace execution layer | `RenameEngine.rename()` never reached | Problem is in Plan generation, not execution |
| 5 | Inspect step 3 conflict detection | `plan.target.exists()` returns `True` on Windows for case-only renames | **Root cause located** |
| 6 | Compare pre-M11.2.4 code | Before M11.2.4, `target.exists()` was the only check — same behavior | Not a new regression from M11.2.4 |
| 7 | Verify on Windows filesystem | Manual check: only `NO.TEST001.txt` exists; no `No.TEST001.txt` | Confirmed: `exists()` is wrong |
| 8 | Research Windows Path behavior | `Path.__eq__` and `Path.exists()` are case-insensitive on Windows | Platform-specific API behavior confirmed |

## 3. Root Cause

Windows filesystems (NTFS, FAT, exFAT) are case-insensitive by default. Python's `pathlib.Path` delegates to the OS filesystem APIs, which means:

- `Path("No.TEST001.txt").exists()` returns `True` when `NO.TEST001.txt` exists (case-insensitive match)
- `Path("NO.TEST001.txt") == Path("No.TEST001.txt")` returns `True` on Windows

The RenamePlan conflict detection used `plan.target.exists()` to check if a file already occupied the target name. On Windows, this returned `True` for case-only renames because the filesystem resolved both paths to the same file. The code then treated this as a genuine conflict and blocked the rename with "目标文件已存在".

```python
# Before fix (simplified)
if plan.target.exists():          # True on Windows for case-only renames
    plan.status = CONFLICT        # Wrong: file is the source itself
```

The fundamental issue: `Path.exists()` alone cannot distinguish between:
- **Case-only rename**: the source and target are the same filesystem object
- **Genuine conflict**: a different file already occupies the target name

## 4. Final Solution

Use `Path.samefile()` to compare filesystem identity rather than path string:

```python
if not plan.target.exists():
    continue
# target.exists() returned True, but it might be the source file itself
# (Windows case-insensitive filesystem). Use samefile() to distinguish.
try:
    if plan.target.samefile(plan.source):
        continue  # Same filesystem object → case-only rename, not a conflict
except OSError:
    pass  # samefile() unavailable → conservative: treat as conflict
# Genuine conflict → apply policy (FAIL / SKIP / OVERWRITE)
```

`Path.samefile()` compares filesystem-level identity:
- **POSIX**: compares `st_dev` + `st_ino` from `os.stat()`
- **Windows**: compares volume serial number + file index from `GetFileInformationByHandle`

If `target` and `source` are the same filesystem object → case-only rename → proceed as READY.
If they differ → genuine conflict → apply existing policy.

An additional guard at a higher level handles the trivial case:

```python
if plan.target_name == plan.source_name:    # String comparison, case-sensitive
    plan.action = SKIP                       # Names identical → no-op
```

This catches `ABC.txt` → `ABC.txt` (same case) early, before any filesystem access.

## 5. Validation

### Manual Windows Verification

```
Initial:  NO.TEST001.txt
Rule:     NO. → No.
Preview:  No.TEST001.txt ✓
Plan:     READY / RENAME ✓
Execute:  SUCCESS → No.TEST001.txt ✓
```

No "目标文件已存在" error. Rename completes successfully.

### Regression Tests Added

| Test | Scenario | Expected |
|---|---|---|
| `test_case_only_file_rename_is_ready` | `NO.TEST001.txt` → `No.TEST001.txt` | READY / RENAME |
| `test_case_only_dir_rename_is_ready` | `NO.TEST001` → `No.TEST001` | READY / RENAME |
| `test_real_conflict_still_blocked` | `a.txt` → `b.txt` (b.txt exists) | CONFLICT / FAIL |
| `test_same_name_is_skip` | `ABC.txt` → `ABC.txt` | SKIP |
| `test_case_only_rename_is_ready` | `NO.TEST001.txt` → `No.TEST001.txt` | READY / RENAME |

### Full Regression

```
188 passed, 0 failed, 0 errors
```

## 6. Lessons Learned

1. **Filesystem APIs ≠ Business Semantics.** `Path.exists()` means "does the OS resolve this path to an existing object?" — not "does a different file occupy this exact name?" Platform-specific behavior (case sensitivity, symlink resolution, Unicode normalization) can cause APIs to produce unexpected results.

2. **Distinguish name comparison from identity comparison.** String comparison checks whether two names are lexically identical. Filesystem identity (`samefile()`) checks whether two paths point to the same object. These are different questions with different answers on case-insensitive filesystems.

3. **Verify platform-specific behavior on the target OS.** This bug only manifested on Windows. Linux/macOS testing could never have caught it because their filesystems are case-sensitive by default.

4. **Read the implementation before continuing analysis.** After multiple rounds of debug logging and speculative analysis, the root cause was found by reading the actual code line `plan.target.exists()` and understanding what it means on Windows. Direct code inspection is often faster than indirect debugging.

5. **Compare historical versions when a regression is suspected.** Even though this was not a new regression (the `exists()` check existed before M11.2.4), understanding the change history prevented unnecessary reverts.

6. **Preserve investigation history.** The sequence of investigation steps (preview → plan → execution → conflict detection → filesystem API) explains WHY the final solution exists. Future developers who read this document can understand not just WHAT was changed, but WHY alternative approaches were ruled out.

## 7. Related Files

| File | Role |
|---|---|
| `engine/rename_plan_engine.py` | Conflict detection logic (step 3) — where the fix was applied |
| `engine/rename_engine.py` | Rename execution — ruled out as not the cause |
| `tests/test_rename_plan.py` | Regression tests for case-only rename scenarios |
| `docs/knowledge/windows_case_only_rename.md` | This document |

## See Also

- [refresh_after_rename.md](refresh_after_rename.md) — Post-rename data refresh strategy
- [../development/current_status.md](../development/current_status.md) — Current project status
- [../AI/DECISION_LOG.md](../AI/DECISION_LOG.md) — Architecture Decision Records
