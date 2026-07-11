from __future__ import annotations

import tempfile
from pathlib import Path

from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_policy import RenamePolicy


def _file(path: Path, preview: str) -> FileItem:
    return FileItem(
        full_path=path, original_name=path.name,
        base_name=path.stem, extension=path.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _plan(item: FileItem, policy: RenamePolicy = RenamePolicy.FAIL):
    return RenamePlanEngine.generate([item], policy)[0]


class TestRenamePolicy:
    """RenamePolicy 三种策略的单元测试 — 策略在 generate() 阶段决定。"""

    def test_fail_target_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("src")
            blocker = root / "target.txt"; blocker.write_text("blocker")

            plan = _plan(_file(src, "target"), RenamePolicy.FAIL)
            assert plan.status.name == "CONFLICT"
            results = RenameEngine.rename([plan])
            assert not results[0].success
            assert "目标文件已存在" in results[0].message
            assert src.exists()

    def test_skip_target_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("src")
            (root / "target.txt").write_text("blocker")

            plan = _plan(_file(src, "target"), RenamePolicy.SKIP)
            assert plan.action.name == "SKIP"
            results = RenameEngine.rename([plan])
            assert results[0].success
            assert results[0].message == "目标已存在，已跳过"
            assert src.exists()

    def test_overwrite_target_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("src")
            blocker = root / "target.txt"; blocker.write_text("blocker")

            plan = _plan(_file(src, "target"), RenamePolicy.OVERWRITE)
            assert plan.action.name == "OVERWRITE"
            results = RenameEngine.rename([plan])
            assert results[0].success
            assert not src.exists()
            assert (root / "target.txt").read_text() == "src"

    def test_no_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for policy in (RenamePolicy.FAIL, RenamePolicy.SKIP, RenamePolicy.OVERWRITE):
                src = root / f"{policy.name}_a.txt"; src.write_text("hello")
                item = _file(src, f"{policy.name}_target")
                results = RenameEngine.rename([_plan(item, policy)])
                assert results[0].success
                assert not src.exists()
                assert (root / f"{policy.name}_target.txt").read_text() == "hello"
