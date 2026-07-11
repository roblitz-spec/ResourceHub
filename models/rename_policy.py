from __future__ import annotations

from enum import Enum


class RenamePolicy(Enum):
    """目标文件冲突处理策略。"""

    FAIL = "fail"
    SKIP = "skip"
    OVERWRITE = "overwrite"
