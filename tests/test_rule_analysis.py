from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from engine.preview_engine import PreviewEngine
from engine.rule_analysis import RuleAnalysis
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


class TestRuleAnalysisUnit:
    """RuleAnalysis.analyze() 单元测试。"""

    def test_empty_rule(self) -> None:
        r = RuleAnalysis.analyze(Rule(id="r", name="r", steps=[]))
        assert r.uses_index is False
        assert r.uses_metadata is False

    def test_replace_only(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="replace", parameters={"from": "a", "to": "b"}),
        ])
        r = RuleAnalysis.analyze(rule)
        assert r.uses_index is False
        assert r.uses_metadata is False

    def test_number_only(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={}),
        ])
        r = RuleAnalysis.analyze(rule)
        assert r.uses_index is True
        assert r.uses_metadata is False

    def test_date_only(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={}),
        ])
        r = RuleAnalysis.analyze(rule)
        assert r.uses_index is False
        assert r.uses_metadata is True

    def test_number_and_date(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={}),
            RuleStep(type="date", parameters={}),
        ])
        r = RuleAnalysis.analyze(rule)
        assert r.uses_index is True
        assert r.uses_metadata is True

    def test_multiple_non_context_steps(self) -> None:
        """多个不需要 context 的 step 组合。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="replace", parameters={}),
            RuleStep(type="trim", parameters={}),
            RuleStep(type="case", parameters={}),
            RuleStep(type="add_prefix", parameters={"text": "X"}),
        ])
        r = RuleAnalysis.analyze(rule)
        assert r.uses_index is False
        assert r.uses_metadata is False

    def test_date_then_number(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={}),
            RuleStep(type="number", parameters={}),
        ])
        r = RuleAnalysis.analyze(rule)
        assert r.uses_index is True
        assert r.uses_metadata is True


class TestPreviewEngineWithAnalysis:
    """PreviewEngine 与 RuleAnalysis 集成测试。"""

    def test_replace_does_not_stat(self) -> None:
        """Replace Rule → PreviewEngine 不创建 MetadataProvider，不调用 stat。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            items = []
            for i in range(10):
                p = root / f"photo_{i}.jpg"
                p.write_text("x")
                items.append(FileItem(
                    full_path=p, original_name=p.name,
                    base_name=p.stem, extension=p.suffix,
                    item_type=ItemType.FILE,
                ))

            with patch("os.stat") as mock_stat:
                rule = Rule(id="r", name="r", steps=[
                    RuleStep(type="replace", parameters={"from": "_", "to": " "}),
                ])
                PreviewEngine.generate_preview(items, rule)
                mock_stat.assert_not_called()

    def test_date_does_stat(self) -> None:
        """Date Rule → PreviewEngine 创建 MetadataProvider，触发 stat。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            p = root / "photo.txt"
            p.write_text("x")
            item = FileItem(
                full_path=p, original_name="photo.txt",
                base_name="photo", extension=".txt",
                item_type=ItemType.FILE,
            )

            with patch("os.stat", wraps=os.stat) as mock_stat:
                rule = Rule(id="r", name="r", steps=[
                    RuleStep(type="date", parameters={}),
                ])
                PreviewEngine.generate_preview([item], rule)
                assert mock_stat.call_count == 1

    def test_number_provides_index(self) -> None:
        """Number Rule → PreviewEngine 提供 index，编号正确。"""
        items = [_file("A.txt"), _file("B.txt"), _file("C.txt")]
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        PreviewEngine.generate_preview(items, rule)
        assert items[0].preview_name == "01_A"
        assert items[1].preview_name == "02_B"
        assert items[2].preview_name == "03_C"

    def test_number_date_combo(self) -> None:
        """Number + Date 组合 → 同时提供 index 和 metadata。"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ts = 1720134000.0
            items = []
            for i in range(3):
                p = root / f"photo_{i}.txt"
                p.write_text("x")
                os.utime(p, (ts, ts))
                items.append(FileItem(
                    full_path=p, original_name=p.name,
                    base_name=p.stem, extension=p.suffix,
                    item_type=ItemType.FILE,
                ))

            rule = Rule(id="r", name="r", steps=[
                RuleStep(type="number", parameters={"padding": "2"}),
                RuleStep(type="date", parameters={"separator": ""}),
            ])
            PreviewEngine.generate_preview(items, rule)
            assert items[0].preview_name.startswith("2024-07-04")
            assert items[1].preview_name.startswith("2024-07-04")
            assert items[2].preview_name.startswith("2024-07-04")
            # 编号递增
            assert "01_" in items[0].preview_name
            assert "02_" in items[1].preview_name
            assert "03_" in items[2].preview_name
