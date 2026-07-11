from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from engine.operation_logger import OperationLogger
from engine.rename_plan_engine import RenamePlanEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_policy import RenamePolicy
from workers.rename_worker import RenameWorker


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def _file(path: Path, preview: str) -> FileItem:
    return FileItem(
        full_path=path, original_name=path.name,
        base_name=path.stem, extension=path.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _plan(item: FileItem):
    return RenamePlanEngine.generate([item])[0]


class TestRenameWorker:
    """RenameWorker 单元测试。"""

    def test_worker_executes(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("hello")
            captured: list = []

            worker = RenameWorker([_plan(_file(src, "renamed"))])
            worker.finished_with_result.connect(lambda r: captured.extend(r), Qt.DirectConnection)
            worker.start()
            worker.wait()

            assert len(captured) == 1
            assert captured[0].success
            assert not src.exists()
            assert (root / "renamed.txt").exists()

    def test_signal_receives_results(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "x.txt"; src.write_text("data")
            captured: list = []

            worker = RenameWorker([_plan(_file(src, "y"))])
            worker.finished_with_result.connect(captured.extend, Qt.DirectConnection)
            worker.start()
            worker.wait()

            assert len(captured) == 1
            assert captured[0].source == src
            assert captured[0].target == root / "y.txt"

    def test_exception_does_not_crash(self, qapp: QApplication) -> None:
        captured: list = []

        # 不存在的源文件 → RenameEngine 内部捕获，返回 failed 结果
        ghost = FileItem(
            full_path=Path("/nonexistent/file.txt"),
            original_name="file.txt", base_name="file", extension=".txt",
            item_type=ItemType.FILE, preview_name="target",
        )
        worker = RenameWorker([_plan(ghost)])
        worker.finished_with_result.connect(captured.extend, Qt.DirectConnection)
        worker.start()
        worker.wait()

        assert len(captured) == 1
        assert not captured[0].success
