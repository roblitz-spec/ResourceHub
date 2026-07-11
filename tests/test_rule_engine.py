from __future__ import annotations

from pathlib import Path

from engine.rule_engine import RuleEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rule import Rule
from models.rule_step import RuleStep


def _make_file(name: str) -> FileItem:
    p = Path(f"/fake/{name}")
    stem = p.stem
    suffix = p.suffix
    return FileItem(
        full_path=p,
        original_name=name,
        base_name=stem,
        extension=suffix,
        item_type=ItemType.FILE,
    )


class TestRuleEngine:
    """RuleEngine 单元测试。"""

    def test_replace(self) -> None:
        item = _make_file("Movie_01.mkv")
        rule = Rule(
            id="r1", name="replace",
            steps=[RuleStep(type="replace", parameters={"from": "_", "to": " "})],
        )
        result = RuleEngine.apply(item, rule)
        assert result == "Movie 01"

    def test_remove_text(self) -> None:
        item = _make_file("Movie_1080p.mkv")
        rule = Rule(
            id="r2", name="remove",
            steps=[RuleStep(type="remove_text", parameters={"text": "1080p"})],
        )
        result = RuleEngine.apply(item, rule)
        assert result == "Movie_"

    def test_add_prefix(self) -> None:
        item = _make_file("Movie.mkv")
        rule = Rule(
            id="r3", name="prefix",
            steps=[RuleStep(type="add_prefix", parameters={"text": "[电影]"})],
        )
        result = RuleEngine.apply(item, rule)
        assert result == "[电影]Movie"

    def test_multi_step(self) -> None:
        """replace → remove_text → add_prefix 组合。"""
        item = _make_file("三体_S01E01_1080p.mkv")
        rule = Rule(
            id="r4", name="combo",
            steps=[
                RuleStep(type="replace", parameters={"from": "_", "to": " "}),
                RuleStep(type="remove_text", parameters={"text": "1080p"}),
                RuleStep(type="add_prefix", parameters={"text": "[国产]"}),
            ],
        )
        result = RuleEngine.apply(item, rule)
        assert result == "[国产]三体 S01E01 "
