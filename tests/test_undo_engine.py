from __future__ import annotations

import tempfile
from pathlib import Path

from engine.operation_logger import OperationLogger
from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from engine.undo_engine import UndoEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_policy import RenamePolicy
from models.rename_result import RenameResult


def _file(path: Path, preview: str) -> FileItem:
    return FileItem(
        full_path=path, original_name=path.name,
        base_name=path.stem, extension=path.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _plan(item: FileItem):
    return RenamePlanEngine.generate([item])[0]


class TestUndoEngine:
    """UndoEngine 单元测试。"""

    def test_single_file_undo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "old.txt"; src.write_text("hello")
            logger = OperationLogger()

            item = _file(src, "new")
            results = RenameEngine.rename([_plan(item)], logger=logger)
            assert results[0].success
            assert not src.exists()
            assert (root / "new.txt").exists()

            # 撤销
            undo_results = UndoEngine.undo(logger)
            assert undo_results[0].success
            assert src.exists()
            assert src.read_text() == "hello"
            assert not (root / "new.txt").exists()

    def test_multi_file_reverse_order(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = root / "a.txt"; a.write_text("1")
            b = root / "b.txt"; b.write_text("2")
            logger = OperationLogger()

            RenameEngine.rename([_plan(_file(a, "ra")), _plan(_file(b, "rb"))], logger=logger)
            assert not a.exists()
            assert not b.exists()

            undo_results = UndoEngine.undo(logger)
            assert undo_results[0].success
            assert undo_results[1].success
            # 逆序：先恢复 b，再恢复 a
            assert undo_results[0].source == root / "rb.txt"
            assert undo_results[0].target == b
            assert undo_results[1].source == root / "ra.txt"
            assert undo_results[1].target == a
            assert a.exists() and b.exists()

    def test_failure_skipped(self) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(
            source=Path("/a/x.txt"), target=Path("/a/y.txt"),
            success=False, message="目标文件已存在",
        ))
        logger.record(RenameResult(
            source=Path("/a/z.txt"), target=Path("/a/w.txt"),
            success=True,
        ))
        # 只有成功记录可撤销
        assert len(UndoEngine.undo(logger)) == 1

    def test_skip_message_skipped(self) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(
            source=Path("/a/x.txt"), target=Path("/a/y.txt"),
            success=True, message="已跳过",
        ))
        assert len(UndoEngine.undo(logger)) == 0

    def test_directory_skipped(self) -> None:
        logger = OperationLogger()
        # 目录：source == target
        logger.record(RenameResult(
            source=Path("/a/dir"), target=Path("/a/dir"),
            success=True,
        ))
        assert len(UndoEngine.undo(logger)) == 0

    def test_clear_after_undo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "old.txt"; src.write_text("x")
            logger = OperationLogger()
            RenameEngine.rename([_plan(_file(src, "new"))], logger=logger)
            assert len(logger.records()) == 1

            UndoEngine.undo(logger)
            assert len(logger.records()) == 0
