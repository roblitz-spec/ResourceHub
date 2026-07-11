from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

from engine.operation_logger import OperationLogger
from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
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


class TestOperationLogger:
    """OperationLogger 单元测试。"""

    def test_success_record(self) -> None:
        logger = OperationLogger()
        r = RenameResult(source=Path("/a/old.txt"), target=Path("/a/new.txt"),
                         success=True)
        logger.record(r)
        records = logger.records()
        assert len(records) == 1
        assert records[0].success
        assert records[0].source == Path("/a/old.txt")
        assert records[0].target == Path("/a/new.txt")
        assert isinstance(records[0].timestamp, datetime)

    def test_failure_record(self) -> None:
        logger = OperationLogger()
        r = RenameResult(source=Path("/a/x.txt"), target=Path("/a/y.txt"),
                         success=False, message="目标文件已存在")
        logger.record(r)
        records = logger.records()
        assert len(records) == 1
        assert not records[0].success
        assert records[0].message == "目标文件已存在"

    def test_skip_record(self) -> None:
        logger = OperationLogger()
        r = RenameResult(source=Path("/a/x.txt"), target=Path("/a/y.txt"),
                         success=True, message="已跳过")
        logger.record(r)
        records = logger.records()
        assert records[0].success
        assert records[0].message == "已跳过"

    def test_clear(self) -> None:
        logger = OperationLogger()
        logger.record(RenameResult(source=Path("a"), target=Path("b"), success=True))
        assert len(logger.records()) == 1
        logger.clear()
        assert len(logger.records()) == 0

    def test_engine_integration(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("hello")
            logger = OperationLogger()

            item = _file(src, "renamed")
            results = RenameEngine.rename([_plan(item)], logger=logger)
            assert results[0].success

            records = logger.records()
            assert len(records) == 1
            assert records[0].success
            assert records[0].source == src
            assert records[0].target == root / "renamed.txt"
