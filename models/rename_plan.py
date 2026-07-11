from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class RenamePlanStatus(Enum):
    NO_CHANGE = auto()   # 目标与源文件名相同
    READY = auto()       # 可执行
    INVALID = auto()     # 非法名称 / 保留名 / 尾部空格点
    CONFLICT = auto()    # 目标冲突（重名 / 大小写）
    SKIPPED = auto()     # 策略 SKIP + 目标已存在
    FAILED = auto()      # 执行失败
    OVERWRITTEN = auto() # 覆盖成功（OVERWRITE 策略）
    SUCCESS = auto()     # 执行成功


class RenameAction(Enum):
    RENAME = auto()      # 执行 Path.rename()
    SKIP = auto()        # 不执行
    FAIL = auto()        # 阻止
    OVERWRITE = auto()   # 先 unlink 再 rename


@dataclass
class RenamePlan:
    """单条重命名计划 —— 包含完整执行决策。"""

    source: Path
    source_name: str
    target_name: str
    target: Path
    needs_rename: bool = False
    status: RenamePlanStatus = RenamePlanStatus.NO_CHANGE
    action: RenameAction = RenameAction.SKIP
    message: str = ""
