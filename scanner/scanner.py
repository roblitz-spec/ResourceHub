from __future__ import annotations

import os
from pathlib import Path
from stat import S_ISDIR, S_ISREG

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

            # 单次 stat，避免 is_dir() + is_file() 重复文件系统访问
            try:
                st = p.stat()
            except OSError:
                continue

            if S_ISDIR(st.st_mode):
                dirs.extend(Scanner._scan_dir(p, seen))
            elif S_ISREG(st.st_mode):
                original_name = p.name
                files.append(FileItem(
                    full_path=p,
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
            # ═══════════════════════════════════════════════════════════
            # PERFORMANCE CRITICAL — DO NOT ADD Path.resolve() HERE
            #
            # os.scandir() returns DirEntry objects where .path is
            # already an absolute path (directory + entry name).
            # Using Path(entry.path) directly avoids filesystem I/O.
            #
            # Path.resolve() calls os.path.realpath(), which traverses
            # every path component with lstat(). On network filesystems
            # (SMB/NAS/WebDAV/FUSE), each lstat is one network round
            # trip (typically 50-200ms).
            #
            # HISTORICAL REGRESSION CASE (2026-07):
            #   605 directories on real SMB NAS:
            #     with .resolve():    252.524s
            #     without .resolve():   0.494s  (≈511× faster)
            #
            # This was a production performance incident. The fix is
            # verified on real NAS hardware. DO NOT reintroduce
            # resolve(), realpath(), or any per-entry stat/is_dir/is_file
            # calls on external paths in this loop.
            #
            # The test_suite includes a regression test that asserts
            # Path.resolve() is NOT called during scan. Any change
            # that reintroduces resolve() will fail CI.
            # ═══════════════════════════════════════════════════════════
            entry_path = Path(entry.path)
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
                files.append(FileItem(
                    full_path=entry_path,
                    original_name=original_name,
                    base_name=Path(entry.name).stem,
                    extension=Path(entry.name).suffix,
                    item_type=ItemType.FILE,
                ))

        return dirs + files
