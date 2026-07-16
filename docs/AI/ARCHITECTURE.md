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
| `PreviewEngine` | Iterates items, provides context via RuleAnalysis, calls RuleEngine | No rename execution |
| `RuleAnalysis` | Declares which context resources a Rule requires | No knowledge of MetadataProvider internals |
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
4. Context fields (`index`, `metadata`) are immutable once frozen
5. New Rule types require only: handler registration + UI entry + tests

## Rule Dependency Analysis

`RuleAnalysis` 在 Preview 循环外分析 Rule 的 context 需求，PreviewEngine 据此按需构造 context。

### 职责

| 角色 | 职责 |
|---|---|
| **RuleAnalysis** | 声明 Rule 需要哪些 context 资源（`uses_index` / `uses_metadata`） |
| **PreviewEngine** | 唯一 Context Owner — 根据 RuleAnalysis 结果按需构造 `ctx` |
| **RuleEngine** | 不依赖 RuleAnalysis — 仅消费 `ctx`，缺失字段时使用内置 fallback |
| **MetadataProvider** | 惰性元数据提供 — RuleAnalysis 不关心其内部字段结构 |

### 扩展规则

新增 Rule 类型时，如需新的 context 资源：

1. 在 `RuleAnalysis` 中新增对应的 `bool` 字段
2. 在 `RuleAnalysis.analyze()` 中新增对应的 step type 判断
3. 在 `PreviewEngine` 中根据新字段条件构造 context

**不得修改 RuleEngine 或 handler 的 context 消费逻辑。**

## Multiple Selection Support

M11.1 引入多选支持。Scanner 是唯一资源聚合入口，Rename Pipeline 完全不变。

### Scanner API

```python
Scanner.scan(paths: list[Path]) → list[FileItem]
```

| 输入类型 | 处理方式 |
|---|---|
| 目录 | `os.scandir()` 扫描直接子项 |
| 文件 | 直接构造 `FileItem` |
| 混合 | 合并为统一列表，自动去重 |

输出顺序：目录在前，文件在后（按名称排序）。

### Resource Aggregation

```
  [Path, Path, ...]
        │
   Scanner.scan()
        │
   list[FileItem]     ← 统一资源列表
        │
   Preview Pipeline   ← 完全不变
```

### Pipeline (Unchanged)

```
PreviewEngine → RenamePlanEngine → RenameEngine → UndoEngine
```

Scanner 是唯一负责资源聚合的模块。Pipeline 各层不区分资源的原始输入方式。多选、单选、单目录、多目录均通过**相同的 FileItem 列表**进入管道。
