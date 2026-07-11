from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    """单个条目的校验结果。"""

    file_path: Path
    is_valid: bool
    message: str = ""
