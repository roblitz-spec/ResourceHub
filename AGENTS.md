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
