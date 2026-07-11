from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class OperationRecord:
    """单次重命名操作的日志记录。"""

    timestamp: datetime = field(default_factory=datetime.now)
    source: Path = Path()
    target: Path = Path()
    success: bool = False
    message: str = ""
