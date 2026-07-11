from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from models.enums import ItemType


@dataclass
class FileItem:
    """文件系统中的单个条目（文件或文件夹）。"""

    full_path: Path
    original_name: str
    base_name: str
    extension: str
    item_type: ItemType
    preview_name: str | None = None
