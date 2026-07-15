from __future__ import annotations

from pathlib import Path

from engine.preview_engine import PreviewEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rule import Rule
from models.rule_step import RuleStep


def _file(name: str) -> FileItem:
    p = Path(f"/fake/{name}")
    return FileItem(
        full_path=p, original_name=name,
        base_name=p.stem, extension=p.suffix,
        item_type=ItemType.FILE,
    )


def _dir(name: str) -> FileItem:
    p = Path(f"/fake/{name}")
    return FileItem(
        full_path=p, original_name=name,
        base_name=name, extension="",
        item_type=ItemType.DIRECTORY,
    )


_RULE = Rule(id="r1", name="test", steps=[
    RuleStep(type="replace", parameters={"from": "_", "to": " "}),
])


class TestPreviewEngine:
    """PreviewEngine 单元测试。"""

    def test_single_file(self) -> None:
        item = _file("Movie_01.mkv")
        PreviewEngine.generate_preview([item], _RULE)
        assert item.preview_name == "Movie 01"

    def test_multiple_files(self) -> None:
        items = [_file("A_B.mkv"), _file("C_D.mp4")]
        PreviewEngine.generate_preview(items, _RULE)
        assert items[0].preview_name == "A B"
        assert items[1].preview_name == "C D"

    def test_directory_preview(self) -> None:
        """目录与文件共用 Preview 管道，目录名也经过 Rule 处理。"""
        items = [_file("A_B.mkv"), _dir("测试文件夹")]
        PreviewEngine.generate_preview(items, _RULE)
        assert items[0].preview_name == "A B"
        assert items[1].preview_name == "测试文件夹"  # 目录名无 _ 故不变

    def test_switch_rule(self) -> None:
        item = _file("Movie_1080p.mkv")
        rule_a = Rule(id="ra", name="a", steps=[
            RuleStep(type="remove_text", parameters={"text": "1080p"}),
        ])
        rule_b = Rule(id="rb", name="b", steps=[
            RuleStep(type="add_prefix", parameters={"text": "[HD]"}),
        ])

        PreviewEngine.generate_preview([item], rule_a)
        assert item.preview_name == "Movie_"

        PreviewEngine.generate_preview([item], rule_b)
        assert item.preview_name == "[HD]Movie_1080p"
