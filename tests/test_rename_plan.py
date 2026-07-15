from __future__ import annotations

from pathlib import Path

from engine.rename_plan_engine import RenamePlanEngine, _check_legality
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_plan import RenamePlanStatus
from models.rename_policy import RenamePolicy


def _file(name: str, preview: str | None = None) -> FileItem:
    p = Path(f"/fake/{name}")
    return FileItem(
        full_path=p, original_name=name,
        base_name=p.stem, extension=p.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


class TestRenamePlan:
    """RenamePlan 生成 & 冲突检测测试。"""

    def test_needs_rename_true(self) -> None:
        plans = RenamePlanEngine.generate([_file("A.txt", "B")])
        assert plans[0].needs_rename
        assert plans[0].target_name == "B.txt"
        assert plans[0].status == RenamePlanStatus.READY

    def test_needs_rename_false(self) -> None:
        plans = RenamePlanEngine.generate([_file("A.txt", "A")])
        assert not plans[0].needs_rename
        assert plans[0].status == RenamePlanStatus.NO_CHANGE

    def test_duplicate_target(self) -> None:
        items = [_file("A.txt", "C"), _file("B.txt", "C")]
        plans = RenamePlanEngine.generate(items)
        assert plans[0].status == RenamePlanStatus.CONFLICT
        assert plans[1].status == RenamePlanStatus.CONFLICT

    def test_forbidden_chars(self) -> None:
        plans = RenamePlanEngine.generate([_file("a.txt", "x:y")])
        assert plans[0].status == RenamePlanStatus.INVALID

    def test_trailing_space(self) -> None:
        plans = RenamePlanEngine.generate([_file("a.txt", "x ")])
        assert plans[0].status == RenamePlanStatus.INVALID

    def test_trailing_dot(self) -> None:
        plans = RenamePlanEngine.generate([_file("a.txt", "x.")])
        assert plans[0].status == RenamePlanStatus.INVALID

    def test_reserved_name(self) -> None:
        plans = RenamePlanEngine.generate([_file("a.txt", "CON")])
        assert plans[0].status == RenamePlanStatus.INVALID

    def test_empty_name(self) -> None:
        plans = RenamePlanEngine.generate([_file("a.txt", "")])
        assert plans[0].status == RenamePlanStatus.INVALID

    def test_all_no_rename(self) -> None:
        items = [_file("A.txt", "A"), _file("B.txt", "B")]
        plans = RenamePlanEngine.generate(items)
        assert all(p.status == RenamePlanStatus.NO_CHANGE for p in plans)

    def test_directory_in_plan(self) -> None:
        """目录与文件共用 RenamePlan 管道。"""
        d = FileItem(
            full_path=Path("/fake/d"), original_name="d",
            base_name="d", extension="", item_type=ItemType.DIRECTORY,
            preview_name="d",
        )
        plans = RenamePlanEngine.generate([d])
        assert plans[0].status == RenamePlanStatus.NO_CHANGE
        assert plans[0].target_name == "d"

    def test_policy_in_plan(self) -> None:
        """RenamePolicy 在 generate 阶段决定 action。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("1")
            (root / "b.txt").write_text("2")  # pre-create target

            item = FileItem(
                full_path=src, original_name="a.txt",
                base_name="a", extension=".txt",
                item_type=ItemType.FILE, preview_name="b",
            )
            # FAIL
            plans = RenamePlanEngine.generate([item], RenamePolicy.FAIL)
            assert plans[0].status == RenamePlanStatus.CONFLICT
            assert plans[0].action == __import__("models.rename_plan", fromlist=["RenameAction"]).RenameAction.FAIL

            # SKIP
            plans = RenamePlanEngine.generate([item], RenamePolicy.SKIP)
            assert plans[0].status == RenamePlanStatus.SKIPPED

            # OVERWRITE
            plans = RenamePlanEngine.generate([item], RenamePolicy.OVERWRITE)
            assert plans[0].status == RenamePlanStatus.READY
            assert plans[0].action.name == "OVERWRITE"


class TestLegality:
    """_check_legality 单元测试。"""

    def test_ok(self) -> None:
        assert _check_legality("Movie 01") == ""

    def test_empty(self) -> None:
        assert "不能为空" in _check_legality("")

    def test_forbidden(self) -> None:
        assert _check_legality("a:b") != ""

    def test_long_name(self) -> None:
        assert _check_legality("A" * 256) != ""

    def test_con_reserved(self) -> None:
        assert _check_legality("CON") != ""
        assert _check_legality("con") != ""  # case insensitive
