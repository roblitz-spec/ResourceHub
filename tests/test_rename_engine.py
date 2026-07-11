from __future__ import annotations

import tempfile
from pathlib import Path

from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from models.enums import ItemType
from models.file_item import FileItem


def _file(path: Path, preview: str) -> FileItem:
    return FileItem(
        full_path=path, original_name=path.name,
        base_name=path.stem, extension=path.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _plan(item: FileItem):
    return RenamePlanEngine.generate([item])[0]


class TestRenameEngine:
    """RenameEngine 单元测试（操作真实临时文件）。"""

    def test_single_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "old_name.txt"
            src.write_text("hello")
            item = _file(src, "new_name")

            results = RenameEngine.rename([_plan(item)])
            assert results[0].success
            assert not src.exists()
            assert (root / "new_name.txt").exists()
            assert (root / "new_name.txt").read_text() == "hello"

    def test_multiple_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = root / "a.txt"; a.write_text("1")
            b = root / "b.txt"; b.write_text("2")

            results = RenameEngine.rename([_plan(_file(a, "renamed_a")), _plan(_file(b, "renamed_b"))])
            assert results[0].success
            assert results[1].success
            assert (root / "renamed_a.txt").exists()
            assert (root / "renamed_b.txt").exists()

    def test_directory_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            d = root / "myfolder"
            d.mkdir()
            dir_item = FileItem(
                full_path=d, original_name="myfolder",
                base_name="myfolder", extension="",
                item_type=ItemType.DIRECTORY, preview_name=None,
            )

            results = RenameEngine.rename([_plan(dir_item)])
            assert results[0].success
            assert results[0].source == d
            assert results[0].target == d
            assert d.exists()

    def test_error_caught(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("1")
            # 目标父目录不存在 → FileNotFoundError
            item = FileItem(
                full_path=src, original_name="a.txt",
                base_name="a", extension=".txt",
                item_type=ItemType.FILE,
                preview_name="nonexistent/sub/target",
            )
            results = RenameEngine.rename([_plan(item)])
            assert not results[0].success
            assert results[0].message != ""
            assert src.exists()  # 源文件未被删除
