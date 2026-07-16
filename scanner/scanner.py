from __future__ import annotations

import os
from pathlib import Path

from models.enums import ItemType
from models.file_item import FileItem


class Scanner:
    """扫描器 —— 支持多路径输入（文件 + 目录混合），不递归。

    使用 os.scandir() 而非 Path.iterdir()：
    在 Windows/SMB 上，os.DirEntry.is_dir() 使用 FindFirstFile 返回的
    缓存属性，避免每次调用触发网络 stat。
    """

    @staticmethod
    def scan(paths: list[Path]) -> list[FileItem]:
        """扫描多个路径，合并为一个 FileItem 列表。

        目录 → 扫描其直接子项。
        文件 → 直接构造 FileItem。
        结果去重（按 full_path），目录在前、文件在后。
        """
        seen: set[Path] = set()
        dirs: list[FileItem] = []
        files: list[FileItem] = []

        for p in paths:
            if p in seen:
                continue
            seen.add(p)

            if p.is_dir():
                dirs.extend(Scanner._scan_dir(p, seen))
            elif p.is_file():
                original_name = p.name
                files.append(FileItem(
                    full_path=p.resolve(),
                    original_name=original_name,
                    base_name=p.stem,
                    extension=p.suffix,
                    item_type=ItemType.FILE,
                ))

        return dirs + files

    @staticmethod
    def _scan_dir(directory: Path, seen: set[Path]) -> list[FileItem]:
        dirs: list[FileItem] = []
        files: list[FileItem] = []

        try:
            with os.scandir(directory) as it:
                entries = sorted(it, key=lambda e: e.name.lower())
        except OSError:
            return []

        for entry in entries:
            entry_path = Path(entry.path).resolve()
            if entry_path in seen:
                continue
            seen.add(entry_path)

            original_name = entry.name
            if entry.is_dir():
                dirs.append(FileItem(
                    full_path=entry_path,
                    original_name=original_name,
                    base_name=original_name,
                    extension="",
                    item_type=ItemType.DIRECTORY,
                ))
            else:
                p = Path(entry.path)
                files.append(FileItem(
                    full_path=entry_path,
                    original_name=original_name,
                    base_name=p.stem,
                    extension=p.suffix,
                    item_type=ItemType.FILE,
                ))

        return dirs + files
