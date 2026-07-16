from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from models.enums import ItemType
from models.rule import Rule
from models.rule_step import RuleStep
from scanner.scanner import Scanner
from workers.scan_worker import ScanWorker


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


class TestScanWorker:
    """ScanWorker + Scanner 性能验证测试。"""

    def test_no_recursive_scan(self) -> None:
        """验证只扫描当前目录，不递归子目录。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.txt").touch()
            sub = root / "sub"
            sub.mkdir()
            (sub / "b.txt").touch()

            items = Scanner.scan([root])
            names = {i.original_name for i in items}
            assert "a.txt" in names
            assert "sub" in names
            assert "b.txt" not in names  # 子目录文件不应出现
            assert len(items) == 2

    def test_worker_produces_preview(self, qapp: QApplication) -> None:
        """ScanWorker 在后台完成扫描 + 预览。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "A_B.txt").touch()
            rule = Rule(id="r", name="r", steps=[
                RuleStep(type="replace", parameters={"from": "_", "to": " "}),
            ])

            worker = ScanWorker([root], rule)
            worker.start()
            worker.wait()

            assert len(worker.items) == 1
            assert worker.items[0].preview_name == "A B"

    def test_worker_handles_missing_dir(self, qapp: QApplication) -> None:
        """不存在的目录不崩溃。"""
        worker = ScanWorker([Path("/nonexistent/path")])
        worker.start()
        worker.wait()
        assert worker.items == []

    def test_repeat_scan_no_thread_warning(self, qapp: QApplication) -> None:
        """重复扫描不触发 QThread destroyed 警告。"""
        import warnings, io, sys

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(5):
                (root / f"file_{i}.txt").touch()

            # 捕获 stderr 中的 Qt 警告
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()

            try:
                for _ in range(3):
                    worker = ScanWorker([root])
                    worker.start()
                    worker.wait()
                    worker.deleteLater()
                    QApplication.processEvents()
            finally:
                output = sys.stderr.getvalue()
                sys.stderr = old_stderr

            assert "Destroyed while thread is still running" not in output

    def test_rename_worker_no_thread_warning(self, qapp: QApplication) -> None:
        """RenameWorker 生命周期不触发线程警告。"""
        import warnings, io, sys

        from engine.rename_engine import RenameEngine
        from engine.rename_plan_engine import RenamePlanEngine
        from models.file_item import FileItem
        from workers.rename_worker import RenameWorker

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for i in range(3):
                p = root / f"old_{i}.txt"; p.write_text("x")

            items = []
            for i in range(3):
                p = root / f"old_{i}.txt"
                items.append(FileItem(
                    full_path=p, original_name=f"old_{i}.txt",
                    base_name=f"old_{i}", extension=".txt",
                    item_type=ItemType.FILE, preview_name=f"new_{i}",
                ))
            plans = RenamePlanEngine.generate(items)

            old_stderr = sys.stderr
            sys.stderr = io.StringIO()

            try:
                for _ in range(2):
                    w = RenameWorker(plans)
                    w.start()
                    w.wait()
                    w.deleteLater()
                    QApplication.processEvents()
            finally:
                output = sys.stderr.getvalue()
                sys.stderr = old_stderr

            assert "Destroyed while thread is still running" not in output
