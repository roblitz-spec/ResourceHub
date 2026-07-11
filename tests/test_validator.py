from __future__ import annotations

from pathlib import Path

from models.enums import ItemType
from models.file_item import FileItem
from validator.validator import Validator


def _file(name: str, preview: str | None = None) -> FileItem:
    p = Path(f"/fake/{name}")
    return FileItem(
        full_path=p, original_name=name,
        base_name=p.stem, extension=p.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _dir(name: str) -> FileItem:
    p = Path(f"/fake/{name}")
    return FileItem(
        full_path=p, original_name=name,
        base_name=name, extension="",
        item_type=ItemType.DIRECTORY, preview_name=None,
    )


class TestValidator:
    """Validator 单元测试。"""

    def test_valid_name(self) -> None:
        results = Validator.validate([_file("a.mkv", "Movie 01")])
        assert len(results) == 1
        assert results[0].is_valid
        assert results[0].message == ""

    def test_empty_name(self) -> None:
        results = Validator.validate([_file("a.mkv", "")])
        assert not results[0].is_valid
        assert results[0].message == "名称不能为空"

    def test_none_name(self) -> None:
        results = Validator.validate([_file("a.mkv", None)])
        assert not results[0].is_valid
        assert results[0].message == "名称不能为空"

    def test_illegal_chars(self) -> None:
        results = Validator.validate([_file("a.mkv", "Movie:01")])
        assert not results[0].is_valid
        assert results[0].message == "包含非法字符"

    def test_too_long(self) -> None:
        long_name = "A" * 256
        results = Validator.validate([_file("a.mkv", long_name)])
        assert not results[0].is_valid
        assert results[0].message == "名称过长"

    def test_duplicate(self) -> None:
        items = [
            _file("A.txt", "Movie"),
            _file("B.txt", "Movie"),
        ]
        results = Validator.validate(items)
        assert not results[0].is_valid
        assert results[0].message == "目标名称重复"
        assert not results[1].is_valid
        assert results[1].message == "目标名称重复"

    def test_multiple_valid(self) -> None:
        results = Validator.validate([
            _file("a.mkv", "Movie 01"),
            _file("b.mp4", "Movie 02"),
        ])
        assert results[0].is_valid
        assert results[1].is_valid

    def test_directory_skipped(self) -> None:
        results = Validator.validate([
            _file("a.mkv", "Movie 01"),
            _dir("测试文件夹"),
        ])
        assert results[0].is_valid
        assert results[1].is_valid
        assert results[1].message == ""
