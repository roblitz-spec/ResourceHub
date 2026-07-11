from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from engine.operation_logger import OperationLogger
from models.rename_result import RenameResult
from ui.operation_log_dialog import OperationLogDialog


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


class TestOperationLogDialog:
    """OperationLogDialog 单元测试。"""

    def test_empty_log(self, qapp: QApplication) -> None:
        logger = OperationLogger()
        dialog = OperationLogDialog(logger)
        assert dialog._table.rowCount() == 0

    def test_success_record(self, qapp: QApplication) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(
            source=Path("/a/old.txt"), target=Path("/a/new.txt"),
            success=True,
        ))
        dialog = OperationLogDialog(logger)
        assert dialog._table.rowCount() == 1
        assert dialog._table.item(0, 3).text() == "成功"

    def test_failure_record(self, qapp: QApplication) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(
            source=Path("/a/x.txt"), target=Path("/a/y.txt"),
            success=False, message="目标文件已存在",
        ))
        dialog = OperationLogDialog(logger)
        assert dialog._table.item(0, 3).text() == "失败"
        assert dialog._table.item(0, 4).text() == "目标文件已存在"

    def test_skip_record(self, qapp: QApplication) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(
            source=Path("/a/a.txt"), target=Path("/a/b.txt"),
            success=True, message="已跳过",
        ))
        dialog = OperationLogDialog(logger)
        assert dialog._table.item(0, 3).text() == "跳过"

    def test_clear(self, qapp: QApplication) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(
            source=Path("/a/old.txt"), target=Path("/a/new.txt"),
            success=True,
        ))
        dialog = OperationLogDialog(logger)
        assert dialog._table.rowCount() == 1

        dialog._on_clear()
        assert dialog._table.rowCount() == 0
        assert len(logger.records()) == 0
