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

    def test_source_equals_target_is_skip(self) -> None:
        """source == target 时应为 SKIP，而非 CONFLICT。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("1")

            item = FileItem(
                full_path=src, original_name="a.txt",
                base_name="a", extension=".txt",
                item_type=ItemType.FILE, preview_name="a",
            )
            plans = RenamePlanEngine.generate([item])
            assert plans[0].status == RenamePlanStatus.NO_CHANGE
            assert plans[0].action.name == "SKIP"

    def test_case_only_rename_is_ready(self) -> None:
        """大小写变更应视为有效 RENAME（非 SKIP）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "NO.TEST001.txt"; src.write_text("1")

            item = FileItem(
                full_path=src, original_name="NO.TEST001.txt",
                base_name="NO.TEST001", extension=".txt",
                item_type=ItemType.FILE, preview_name="No.TEST001",
            )
            plans = RenamePlanEngine.generate([item])
            assert plans[0].status == RenamePlanStatus.READY
            assert plans[0].action.name == "RENAME"
            assert plans[0].target_name == "No.TEST001.txt"

    def test_same_name_is_skip(self) -> None:
        """完全相同名称应 SKIP。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "ABC.txt"; src.write_text("1")

            item = FileItem(
                full_path=src, original_name="ABC.txt",
                base_name="ABC", extension=".txt",
                item_type=ItemType.FILE, preview_name="ABC",
            )
            plans = RenamePlanEngine.generate([item])
            assert plans[0].status == RenamePlanStatus.NO_CHANGE
            assert plans[0].action.name == "SKIP"

    def test_case_only_file_rename_is_ready(self) -> None:
        """大小写文件重命名应 READY（非 CONFLICT）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "NO.TEST001.txt"; src.write_text("1")

            item = FileItem(
                full_path=src, original_name="NO.TEST001.txt",
                base_name="NO.TEST001", extension=".txt",
                item_type=ItemType.FILE, preview_name="No.TEST001",
            )
            plans = RenamePlanEngine.generate([item])
            assert plans[0].status == RenamePlanStatus.READY
            assert plans[0].action.name == "RENAME"

    def test_case_only_dir_rename_is_ready(self) -> None:
        """大小写目录重命名应 READY（非 CONFLICT）。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "NO.TEST001"
            src.mkdir()

            item = FileItem(
                full_path=src, original_name="NO.TEST001",
                base_name="NO.TEST001", extension="",
                item_type=ItemType.DIRECTORY, preview_name="No.TEST001",
            )
            plans = RenamePlanEngine.generate([item])
            assert plans[0].status == RenamePlanStatus.READY
            assert plans[0].action.name == "RENAME"

    def test_real_conflict_still_blocked(self) -> None:
        """真实冲突（不同文件同名）仍应 CONFLICT。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("1")
            (root / "b.txt").write_text("2")  # pre-existing target

            item = FileItem(
                full_path=src, original_name="a.txt",
                base_name="a", extension=".txt",
                item_type=ItemType.FILE, preview_name="b",
            )
            plans = RenamePlanEngine.generate([item])
            assert plans[0].status == RenamePlanStatus.CONFLICT
            assert plans[0].action.name == "FAIL"


class TestPreviewRenameConsistency:
    """Preview → Rename 一致性（排序/刷新后不变）。"""

    def _make_items(self, root: Path) -> list[FileItem]:
        items = []
        for name in ["C.txt", "A.txt", "B.txt"]:
            p = root / name; p.write_text("x")
            items.append(FileItem(
                full_path=p, original_name=name,
                base_name=p.stem, extension=p.suffix,
                item_type=ItemType.FILE,
            ))
        return items

    def test_sort_then_rename(self) -> None:
        import tempfile
        from engine.preview_engine import PreviewEngine
        from models.rule import Rule
        from models.rule_step import RuleStep

        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="add_prefix", parameters={"text": "X_"}),
        ])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            items = self._make_items(root)
            PreviewEngine.generate_preview(items, rule)
            plans = RenamePlanEngine.generate(items)
            names = {p.target_name for p in plans if p.status == RenamePlanStatus.READY}
            assert names == {"X_A.txt", "X_B.txt", "X_C.txt"}

    def test_refresh_then_rename(self) -> None:
        import tempfile
        from engine.preview_engine import PreviewEngine
        from models.rule import Rule
        from models.rule_step import RuleStep

        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="add_prefix", parameters={"text": "Y_"}),
        ])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            items = self._make_items(root)
            PreviewEngine.generate_preview(items, rule)
            PreviewEngine.generate_preview(items, rule)
            plans = RenamePlanEngine.generate(items)
            names = {p.target_name for p in plans if p.status == RenamePlanStatus.READY}
            assert names == {"Y_A.txt", "Y_B.txt", "Y_C.txt"}

    def test_source_unchanged_after_preview(self) -> None:
        import tempfile
        from engine.preview_engine import PreviewEngine
        from models.rule import Rule
        from models.rule_step import RuleStep

        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="add_prefix", parameters={"text": "Z_"}),
        ])
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            items = self._make_items(root)
            original_paths = {i.full_path for i in items}
            original_names = {i.original_name for i in items}
            for _ in range(3):
                PreviewEngine.generate_preview(items, rule)
            assert {i.full_path for i in items} == original_paths
            assert {i.original_name for i in items} == original_names


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
