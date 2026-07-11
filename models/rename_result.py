from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class RenameResult:
    """单次重命名操作的结果。"""

    source: Path
    target: Path
    success: bool
    message: str = ""
