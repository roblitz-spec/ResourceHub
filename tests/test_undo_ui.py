from __future__ import annotations

import tempfile
from pathlib import Path

from engine.operation_logger import OperationLogger
from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from engine.undo_engine import UndoEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_result import RenameResult


def _file(path: Path, preview: str) -> FileItem:
    return FileItem(
        full_path=path, original_name=path.name,
        base_name=path.stem, extension=path.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _plan(item: FileItem):
    return RenamePlanEngine.generate([item])[0]


class TestUndoUI:
    """Undo UI 逻辑的集成测试（不依赖 QWidget）。"""

    def test_no_log_undo_disabled(self) -> None:
        logger = OperationLogger()
        assert len(logger.records()) == 0

    def test_rename_success_enables_undo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("1")
            logger = OperationLogger()

            results = RenameEngine.rename([_plan(_file(src, "renamed"))], logger=logger)
            assert results[0].success
            assert len(logger.records()) == 1

    def test_undo_restores_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "old.txt"; src.write_text("data")
            logger = OperationLogger()

            RenameEngine.rename([_plan(_file(src, "new"))], logger=logger)
            assert not src.exists()

            results = UndoEngine.undo(logger)
            assert results[0].success
            assert src.exists()
            assert src.read_text() == "data"

    def test_undo_clears_log(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "x.txt"; src.write_text("ok")
            logger = OperationLogger()

            RenameEngine.rename([_plan(_file(src, "y"))], logger=logger)
            assert len(logger.records()) == 1

            UndoEngine.undo(logger)
            assert len(logger.records()) == 0

    def test_undo_target_missing_skipped(self) -> None:
        """Undo 时目标文件已被删除 → skip 该项。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "old.txt"; src.write_text("data")
            logger = OperationLogger()

            # 改名后删除目标文件
            RenameEngine.rename([_plan(_file(src, "new"))], logger=logger)
            (root / "new.txt").unlink()

            results = UndoEngine.undo(logger)
            assert not results[0].success  # 目标不存在 → 失败

    def test_double_undo_no_op(self) -> None:
        """Undo 后再次 Undo → 日志为空，无操作。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("ok")
            logger = OperationLogger()

            RenameEngine.rename([_plan(_file(src, "b"))], logger=logger)
            UndoEngine.undo(logger)  # 第一次 undo 成功
            # 第二次 undo — logger 已清空
            results = UndoEngine.undo(logger)
            assert len(results) == 0
