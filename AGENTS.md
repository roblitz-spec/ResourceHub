# ResourceHub — 开发参考

## Git 基线

| Tag | 内容 |
|---|---|
| `M12-complete` | Number Rule 完成，122 tests |
| `M13-complete` | Insert Rule 完成，131 tests |

## RuleStep 类型总览

| type | 中文 | 参数 | 默认值 |
|---|---|---|---|
| `replace` | 文本替换 | `from`, `to` | `""`, `""` |
| `remove_text` | 删除文本 | `text` | `""` |
| `regex_replace` | 正则替换 | `pattern`, `replacement`, `flags` | `""`, `""`, `""` |
| `case` | 大小写转换 | `mode` | `"upper"` |
| `trim` | 去除空白 | `mode` | `"both"` |
| `number` | 编号 | `start`, `step`, `padding`, `position` | `"1"`, `"1"`, `"3"`, `"prefix"` |
| `insert` | 插入文本 | `text`, `at_index` | `""`, `"0"` |
| `add_prefix` | 添加前缀 | `text` | `""` |

## Insert Rule 行为规范

- `at_index = 0` → 插入到开头
- `at_index = N (0 < N ≤ len)` → 插入到第 N 个字符后
- `at_index > len` → clamp 到末尾
- `at_index < 0`（任意负数）→ clamp 到末尾
- `text = ""` → 不改变原文字
- Step 顺序严格按列表执行，Insert 不例外

## Number Rule 行为规范

- `index` 由 PreviewEngine 提供（1-based），非 Python 下标
- 无 context 时默认 `index = 1`
- 计算公式：`number = start + (index - 1) * step`
- `padding = 0` → 不补零
- RuleEngine 保持无状态，不存储计数器

## 架构原则

- RuleEngine：纯函数，无状态，通过 `context` 参数传递索引
- RenamePlanEngine：统一生成计划 + 冲突检测 + 合法性校验
- RenameEngine：仅按 `plan.action` 执行，不重复决策
- Preview ↔ Rename 共享同一份 RenamePlan

## Development Workflow

每个 Milestone 统一流程：

### 1. Implementation（实现）
- 小步迭代，每次只完成一个明确目标
- 保持 RuleEngine 纯函数、无状态设计
- 新增 Rule 类型只需注册 `_HANDLERS` + `_STEP_TYPES`，不改架构

### 2. Automated Tests（自动化测试）
- 为新增功能补充对应测试
- 覆盖：默认参数、边界值、Rule 顺序、保存/加载、Preview↔Rename 一致性
- 全部测试通过后进入下一阶段

### 3. Validation（产品行为验证）
- 验证默认参数与产品规范一致
- 验证边界条件（空值、超长、负数等）
- 验证 Rule 顺序语义（Step A → Step B ≠ Step B → Step A）
- 验证保存/加载 roundtrip
- 验证 Preview 显示与实际 Rename 结果一致

### 4. Smoke Test（真实使用验证）
- 使用真实目录进行手工验证
- 验证完整 Rename 流程（Preview → Plan → Rename → 文件确认）
- 验证 UI 行为（不重扫、Preview 自刷新、按钮状态）

### 5. Git Tag（创建基线）
- 当前 Milestone 完成后创建稳定基线
- 命名：`Mxx-complete`
- 目的：后续可快速回退定位

### 6. Feature Freeze（功能冻结）
- 当前 Milestone 完成后冻结相关模块
- 除真实 Bug 外，不修改已冻结模块
- 新功能优先通过新增模块或新增 Rule 实现

### 7. Update AGENTS.md（更新文档）
- 更新新增 Rule 类型、默认参数、行为规范
- 更新 Git 基线记录
- 更新架构说明（如有变化）

### 8. Next Milestone（进入下一阶段）
- 以上步骤全部完成后，方可开始下一 Milestone 开发

### 开发原则

- **小步迭代**：每次只完成一个明确目标
- **测试先行**：先写测试，再写实现，或同步进行
- **稳定基线**：每个 Milestone 锁 Tag、锁行为
- **功能冻结**：完成后不轻易改，只能 Bug Fix
- **文档同步**：行为变更必须更新 AGENTS.md
