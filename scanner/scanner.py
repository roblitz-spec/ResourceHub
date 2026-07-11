from __future__ import annotations

import os
from pathlib import Path

from models.enums import ItemType
from models.file_item import FileItem


class Scanner:
    """目录扫描器 —— 仅扫描当前目录（不递归）。

    使用 os.scandir() 而非 Path.iterdir()：
    在 Windows/SMB 上，os.DirEntry.is_dir() 使用 FindFirstFile 返回的
    缓存属性，避免每次调用触发网络 stat。
    """

    @staticmethod
    def scan(directory: Path) -> list[FileItem]:
        dirs: list[FileItem] = []
        files: list[FileItem] = []

        try:
            with os.scandir(directory) as it:
                entries = sorted(it, key=lambda e: e.name.lower())
        except OSError:
            return []

        for entry in entries:
            original_name = entry.name
            # os.DirEntry.is_dir() 在 Windows 上使用缓存属性，无额外 stat
            if entry.is_dir():
                dirs.append(FileItem(
                    full_path=Path(entry.path),
                    original_name=original_name,
                    base_name=original_name,
                    extension="",
                    item_type=ItemType.DIRECTORY,
                ))
            else:
                p = Path(entry.path)
                files.append(FileItem(
                    full_path=p,
                    original_name=original_name,
                    base_name=p.stem,
                    extension=p.suffix,
                    item_type=ItemType.FILE,
                ))

        return dirs + files
