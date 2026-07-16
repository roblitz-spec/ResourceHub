from __future__ import annotations

import os
import tempfile
from pathlib import Path

from engine.preview_engine import PreviewEngine
from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from engine.undo_engine import UndoEngine
from engine.operation_logger import OperationLogger
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_plan import RenamePlanStatus as S
from models.rule import Rule
from models.rule_step import RuleStep
from scanner.scanner import Scanner


_RULE = Rule(id="r", name="r", steps=[
    RuleStep(type="replace", parameters={"from": "_", "to": " "}),
])


class TestScannerMultiPath:
    """Scanner.scan() 多路径输入测试。"""

    def test_single_directory(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "A.txt").touch()
            (root / "B.txt").touch()
            items = Scanner.scan([root])
            assert len(items) == 2
            assert {i.original_name for i in items} == {"A.txt", "B.txt"}

    def test_multiple_directories(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d1 = root / "dir1"; d1.mkdir(); (d1 / "a.txt").touch()
            d2 = root / "dir2"; d2.mkdir(); (d2 / "b.txt").touch()
            items = Scanner.scan([d1, d2])
            assert len(items) == 2
            assert {i.original_name for i in items} == {"a.txt", "b.txt"}

    def test_single_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "single.txt"; p.write_text("x")
            items = Scanner.scan([p])
            assert len(items) == 1
            assert items[0].original_name == "single.txt"
            assert items[0].item_type == ItemType.FILE

    def test_mixed_files_and_directories(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / "mydir"; d.mkdir()
            (d / "inside.txt").touch()
            f = root / "loose.txt"; f.write_text("x")
            items = Scanner.scan([d, f])
            assert len(items) == 2
            names = {i.original_name for i in items}
            assert "inside.txt" in names
            assert "loose.txt" in names

    def test_deduplication(self) -> None:
        """同一路径多次传入 → 去重。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.txt").touch()
            items = Scanner.scan([root, root])
            assert len(items) == 1

    def test_dirs_before_files(self) -> None:
        """目录排在文件前面。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "sub").mkdir()
            (root / "z.txt").touch()
            items = Scanner.scan([root])
            assert items[0].item_type == ItemType.DIRECTORY
            assert items[1].item_type == ItemType.FILE


class TestMultiSelectPreview:
    """多选 Preview 测试。"""

    def test_preview_multiple_files(self) -> None:
        items = []
        for name in ["A_B.txt", "C_D.txt", "E_F.txt"]:
            p = Path(f"/fake/{name}")
            items.append(FileItem(
                full_path=p, original_name=name,
                base_name=p.stem, extension=p.suffix,
                item_type=ItemType.FILE,
            ))
        PreviewEngine.generate_preview(items, _RULE)
        assert items[0].preview_name == "A B"
        assert items[1].preview_name == "C D"
        assert items[2].preview_name == "E F"

    def test_numbering_continuous(self) -> None:
        """多选文件编号连续。"""
        items = []
        for name in ["A.txt", "B.txt", "C.txt"]:
            p = Path(f"/fake/{name}")
            items.append(FileItem(
                full_path=p, original_name=name,
                base_name=p.stem, extension=p.suffix,
                item_type=ItemType.FILE,
            ))
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        PreviewEngine.generate_preview(items, rule)
        assert items[0].preview_name == "01_A"
        assert items[1].preview_name == "02_B"
        assert items[2].preview_name == "03_C"

    def test_mixed_files_and_folders(self) -> None:
        """文件 + 文件夹混合预览，统一编号。"""
        items = [
            FileItem(full_path=Path("/fake/d"), original_name="d",
                     base_name="d", extension="", item_type=ItemType.DIRECTORY),
            FileItem(full_path=Path("/fake/a.txt"), original_name="a.txt",
                     base_name="a", extension=".txt", item_type=ItemType.FILE),
            FileItem(full_path=Path("/fake/b.txt"), original_name="b.txt",
                     base_name="b", extension=".txt", item_type=ItemType.FILE),
        ]
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        PreviewEngine.generate_preview(items, rule)
        assert items[0].preview_name == "01_d"
        assert items[1].preview_name == "02_a"
        assert items[2].preview_name == "03_b"


class TestMultiSelectRename:
    """多选 Rename E2E 测试。"""

    def test_rename_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            files = []
            for name in ["A_B.txt", "C_D.txt"]:
                p = root / name; p.write_text("x")
                files.append(FileItem(
                    full_path=p, original_name=name,
                    base_name=p.stem, extension=p.suffix,
                    item_type=ItemType.FILE,
                ))
            PreviewEngine.generate_preview(files, _RULE)
            plans = RenamePlanEngine.generate(files)
            assert all(p.status == S.READY for p in plans)

            results = RenameEngine.rename(plans)
            assert all(r.success for r in results)
            assert (root / "A B.txt").exists()
            assert (root / "C D.txt").exists()

    def test_rename_mixed_files_and_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / "my_folder"; d.mkdir()
            f = root / "A_B.txt"; f.write_text("x")

            items = [
                FileItem(full_path=d, original_name="my_folder",
                         base_name="my_folder", extension="",
                         item_type=ItemType.DIRECTORY, preview_name="my folder"),
                FileItem(full_path=f, original_name="A_B.txt",
                         base_name="A_B", extension=".txt",
                         item_type=ItemType.FILE, preview_name="A B"),
            ]
            plans = RenamePlanEngine.generate(items)
            ready = [p for p in plans if p.status == S.READY]
            assert len(ready) == 2

            results = RenameEngine.rename(plans)
            assert all(r.success for r in results)
            assert (root / "my folder").exists()
            assert (root / "A B.txt").exists()

    def test_undo_multiple_rename(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            logger = OperationLogger()
            f1 = root / "old_a.txt"; f1.write_text("x")
            f2 = root / "old_b.txt"; f2.write_text("x")

            items = [
                FileItem(full_path=f1, original_name="old_a.txt",
                         base_name="old_a", extension=".txt",
                         item_type=ItemType.FILE, preview_name="new_a"),
                FileItem(full_path=f2, original_name="old_b.txt",
                         base_name="old_b", extension=".txt",
                         item_type=ItemType.FILE, preview_name="new_b"),
            ]
            plans = RenamePlanEngine.generate(items)
            RenameEngine.rename(plans, logger)

            assert (root / "new_a.txt").exists()
            assert (root / "new_b.txt").exists()

            results = UndoEngine.undo(logger)
            assert all(r.success for r in results)
            assert (root / "old_a.txt").exists()
            assert (root / "old_b.txt").exists()
