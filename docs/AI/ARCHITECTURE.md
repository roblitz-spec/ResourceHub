# ResourceHub — Architecture

## Pipeline

```
File System
    ↓
Scanner (os.scandir, non-recursive)
    ↓ list[FileItem]
PreviewEngine (RuleEngine.apply per item, with context)
    ↓ preview_name on each FileItem
RenamePlanEngine.generate(items, policy)
    ↓ list[RenamePlan] with status/action/message
RenameEngine.rename(plans, logger)
    ↓ list[RenameResult]
OperationLogger (records for Undo)
    ↓
UndoEngine.undo(logger)
```

## Module Boundaries

| Module | Responsibility | Forbidden |
|---|---|---|
| `Scanner` | Directory scan, file type classification | No recursive scan |
| `RuleEngine` | Pure-function text transformation per step | No state, no I/O, no counters |
| `PreviewEngine` | Iterates items, provides context, calls RuleEngine | No rename execution |
| `RenamePlanEngine` | Target computation, legality check, conflict detection, policy application | No file I/O (except `target.exists()`) |
| `RenameEngine` | Execute `plan.action` via `Path.rename()` | No re-computation of targets or policy |
| `UndoEngine` | Reverse rename from OperationLogger records | No multi-level history |
| `FileTableModel` | Qt Model/View data provider | No file system access in `data()` |
| `RuleManagerDialog` | CRUD + RuleStep editing | No direct JSON access (uses Repository) |
| `MainWindow` | Orchestration, button wiring, signal routing | No rename logic, no string processing |

## Hard Rules

1. UI never calls RenameEngine directly — goes through RenameWorker (QThread)
2. RuleEngine handlers never access the file system
3. Preview and Rename share the same RenamePlan target computation
4. Context fields (`index`, `timestamps`) are immutable once frozen
5. New Rule types require only: handler registration + UI entry + tests
