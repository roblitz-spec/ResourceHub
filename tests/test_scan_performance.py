from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

from models.enums import ItemType
from scanner.scanner import Scanner


class TestScanPerformance:
    """Scanner 性能验证测试。"""

    def test_no_recursive(self) -> None:
        """Scanner 不递归子目录。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.txt").touch()
            sub = root / "sub"
            sub.mkdir()
            (sub / "b.txt").touch()

            items = Scanner.scan([root])
            names = {i.original_name for i in items}
            assert "b.txt" not in names
            assert len(items) == 2  # a.txt + sub

    def test_no_redundant_stat(self) -> None:
        """Scanner 不重复调用 stat（通过 os.scandir 缓存属性）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(10):
                (root / f"file_{i}.txt").touch()

            stat_count = 0
            _real_stat = os.stat

            def _counting_stat(path, *args, **kwargs):
                nonlocal stat_count
                stat_count += 1
                return _real_stat(path, *args, **kwargs)

            with patch("os.stat", _counting_stat):
                items = Scanner.scan([root])

            # os.scandir 本身调用 stat，但 is_dir() 使用缓存不调用 stat
            # 每个文件 + 目录本身 + scandir 内部 = O(n) 而非 O(n²)
            assert len(items) == 10
            # scandir 的 stat 调用是内部的，不应超过条目数太多
            assert stat_count <= len(items) + 5, f"Too many stat calls: {stat_count}"

    def test_directory_preview_no_internal_access(self) -> None:
        """PreviewEngine 不对目录执行任何内部访问。"""
        from engine.preview_engine import PreviewEngine
        from models.rule import Rule

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / "mydir"
            d.mkdir()
            (d / "inside.txt").touch()

            item = __import__("models.file_item", fromlist=["FileItem"]).FileItem(
                full_path=d, original_name="mydir",
                base_name="mydir", extension="",
                item_type=ItemType.DIRECTORY, preview_name=None,
            )

            # 记录 scandir/iterdir 调用 — 确保不对目录内部做任何遍历
            with patch("os.scandir") as mock_scandir:
                PreviewEngine.generate_preview([item], Rule(id="r", name="r", steps=[]))
                mock_scandir.assert_not_called()

    def test_scan_completes_normally(self) -> None:
        """普通目录扫描在合理时间内完成。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(100):
                (root / f"f{i}.txt").touch()
            for i in range(10):
                (root / f"d{i}").mkdir()

            t0 = time.monotonic()
            items = Scanner.scan([root])
            elapsed = time.monotonic() - t0

            assert len(items) == 110
            assert elapsed < 1.0, f"Scan too slow: {elapsed:.3f}s"

    def test_first_scan_vs_second_scan(self) -> None:
        """连续两次扫描耗时接近（无首次初始化开销）。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(50):
                (root / f"f{i}.txt").touch()

            t0 = time.monotonic()
            Scanner.scan([root])
            first = time.monotonic() - t0

            t0 = time.monotonic()
            Scanner.scan([root])
            second = time.monotonic() - t0

            # 第二次不应显著慢于第一次（允许 2x 容差）
            assert second <= max(first * 2, 0.1), \
                f"Second scan ({second:.4f}s) much slower than first ({first:.4f}s)"
