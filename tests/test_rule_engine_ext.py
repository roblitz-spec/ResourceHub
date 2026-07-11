from __future__ import annotations

import tempfile
from pathlib import Path

from engine.preview_engine import PreviewEngine
from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from engine.rule_engine import RuleEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_policy import RenamePolicy
from models.rule import Rule
from models.rule_step import RuleStep


def _file_item(base: str, ext: str = ".txt") -> FileItem:
    return FileItem(
        full_path=Path(f"/fake/{base}{ext}"),
        original_name=f"{base}{ext}",
        base_name=base, extension=ext,
        item_type=ItemType.FILE, preview_name=None,
    )


class TestRegexReplace:
    """regex_replace RuleStep 测试。"""

    def test_simple_replace(self) -> None:
        item = _file_item("S01E01_1080p")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="regex_replace", parameters={
                "pattern": r"\d+p$", "replacement": "HD",
            }),
        ])
        result = RuleEngine.apply(item, rule)
        assert result == "S01E01_HD"

    def test_group_replace(self) -> None:
        item = _file_item("Episode_01")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="regex_replace", parameters={
                "pattern": r"Episode_(\d+)", "replacement": r"E\1",
            }),
        ])
        result = RuleEngine.apply(item, rule)
        assert result == "E01"

    def test_invalid_regex_does_not_crash(self) -> None:
        item = _file_item("test")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="regex_replace", parameters={
                "pattern": r"[invalid", "replacement": "x",
            }),
        ])
        result = RuleEngine.apply(item, rule)
        assert result == "test"  # 保持不变


class TestCaseConvert:
    """case RuleStep 测试。"""

    def test_upper(self) -> None:
        item = _file_item("movie_title")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="case", parameters={"mode": "upper"}),
        ])
        assert RuleEngine.apply(item, rule) == "MOVIE_TITLE"

    def test_lower(self) -> None:
        item = _file_item("MOVIE_TITLE")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="case", parameters={"mode": "lower"}),
        ])
        assert RuleEngine.apply(item, rule) == "movie_title"

    def test_title(self) -> None:
        item = _file_item("hello world")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="case", parameters={"mode": "title"}),
        ])
        assert RuleEngine.apply(item, rule) == "Hello World"

    def test_capitalize(self) -> None:
        item = _file_item("hello world")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="case", parameters={"mode": "capitalize"}),
        ])
        assert RuleEngine.apply(item, rule) == "Hello world"


class TestTrim:
    """trim RuleStep 测试。"""

    def test_both(self) -> None:
        item = _file_item("  name  ")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="trim", parameters={"mode": "both"}),
        ])
        assert RuleEngine.apply(item, rule) == "name"

    def test_left(self) -> None:
        item = _file_item("  name  ")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="trim", parameters={"mode": "left"}),
        ])
        assert RuleEngine.apply(item, rule) == "name  "

    def test_right(self) -> None:
        item = _file_item("  name  ")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="trim", parameters={"mode": "right"}),
        ])
        assert RuleEngine.apply(item, rule) == "  name"

    def test_default_both(self) -> None:
        item = _file_item("  x  ")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="trim", parameters={}),
        ])
        assert RuleEngine.apply(item, rule) == "x"


class TestNewRuleE2E:
    """新 Rule 类型端到端测试：Preview → Plan → Rename。"""

    def test_regex_rename_e2e(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "Movie_S01E01.mkv"; src.write_text("hello")

            item = FileItem(
                full_path=src, original_name="Movie_S01E01.mkv",
                base_name="Movie_S01E01", extension=".mkv",
                item_type=ItemType.FILE,
            )
            rule = Rule(id="r", name="r", steps=[
                RuleStep(type="regex_replace", parameters={
                    "pattern": r"_(S\d+E\d+)", "replacement": r" \1",
                }),
            ])

            PreviewEngine.generate_preview([item], rule)
            assert item.preview_name == "Movie S01E01"

            plans = RenamePlanEngine.generate([item])
            assert plans[0].status.name == "READY"

            results = RenameEngine.rename(plans)
            assert results[0].success
            assert (root / "Movie S01E01.mkv").exists()

    def test_case_trim_combo(self) -> None:
        """trim + case 组合。"""
        item = _file_item("  Movie_Title  ")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="trim", parameters={"mode": "both"}),
            RuleStep(type="replace", parameters={"from": "_", "to": " "}),
            RuleStep(type="case", parameters={"mode": "title"}),
        ])
        result = RuleEngine.apply(item, rule)
        assert result == "Movie Title"


class TestNumberRule:
    """Number RuleStep 测试。"""

    def test_default_params_prefix(self) -> None:
        """默认参数：start=1, step=1, padding=3, prefix。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "001_file"
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 2}) == "002_file"
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 3}) == "003_file"

    def test_custom_start_step(self) -> None:
        """start=10, step=5, padding=0。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"start": "10", "step": "5", "padding": "0"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "10_file"
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 2}) == "15_file"
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 3}) == "20_file"

    def test_padding_4(self) -> None:
        """padding=4。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"start": "10", "step": "5", "padding": "4"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "0010_file"
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 2}) == "0015_file"

    def test_suffix(self) -> None:
        """suffix 位置。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"position": "suffix"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "file_001"

    def test_prefix(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"position": "prefix"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "001_file"

    def test_no_context_defaults_to_1(self) -> None:
        """无 context 时默认 index=1。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule) == "001_file"

    def test_number_combo_with_prefix(self) -> None:
        """add_prefix + number 组合。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="add_prefix", parameters={"text": "[HD]"}),
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        result = RuleEngine.apply(_file_item("Movie"), rule, {"index": 1})
        assert result == "01_[HD]Movie"

    def test_preview_e2e(self) -> None:
        """PreviewEngine 传递正确的 index 上下文。"""
        items = [
            _file_item("A", ".txt"), _file_item("B", ".txt"), _file_item("C", ".txt"),
        ]
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={}),
        ])
        PreviewEngine.generate_preview(items, rule)
        assert items[0].preview_name == "001_A"
        assert items[1].preview_name == "002_B"
        assert items[2].preview_name == "003_C"

    def test_step_order_number_then_prefix(self) -> None:
        """Number → Prefix 顺序：先编号再加前缀。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"padding": "2"}),
            RuleStep(type="add_prefix", parameters={"text": "[HD]"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "[HD]01_file"

    def test_step_order_prefix_then_number(self) -> None:
        """Prefix → Number 顺序：先前缀再编号。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="add_prefix", parameters={"text": "[HD]"}),
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule, {"index": 1}) == "01_[HD]file"

    def test_save_load_roundtrip(self) -> None:
        """Number Rule 保存/加载参数完整恢复。"""
        import tempfile
        from pathlib import Path
        from storage.repository import RuleRepository

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            repo = RuleRepository(p)
            repo.load()
            repo.add(Rule(id="r1", name="编号规则", steps=[
                RuleStep(type="number", parameters={
                    "start": "10", "step": "5", "padding": "4", "position": "suffix",
                }),
            ]))
            repo.save()

            repo2 = RuleRepository(p)
            repo2.load()
            r = repo2.find("r1")
            assert r is not None
            s = r.steps[0]
            assert s.parameters["start"] == "10"
            assert s.parameters["step"] == "5"
            assert s.parameters["padding"] == "4"
            assert s.parameters["position"] == "suffix"

class TestInsertRule:
    """Insert RuleStep 测试。"""

    def test_insert_at_beginning(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "X", "at_index": "0"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule) == "Xfile"

    def test_insert_at_end(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "_v2", "at_index": "-1"}),
        ])
        assert RuleEngine.apply(_file_item("file"), rule) == "file_v2"

    def test_insert_in_middle(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "MID", "at_index": "2"}),
        ])
        assert RuleEngine.apply(_file_item("abcdef"), rule) == "abMIDcdef"

    def test_insert_no_text_no_change(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"at_index": "2"}),
        ])
        assert RuleEngine.apply(_file_item("abcdef"), rule) == "abcdef"

    def test_insert_pipeline(self) -> None:
        """insert + number 组合。"""
        items = [_file_item("A", ".txt"), _file_item("B", ".txt")]
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "_", "at_index": "1"}),
            RuleStep(type="number", parameters={"padding": "2", "position": "prefix"}),
        ])
        PreviewEngine.generate_preview(items, rule)
        assert items[0].preview_name == "01_A_"
        assert items[1].preview_name == "02_B_"


    def test_preview_rename_plan_consistency(self) -> None:
        """Preview → RenamePlan 的 target_name 一致。"""
        item = _file_item("file", ".txt")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        PreviewEngine.generate_preview([item], rule)
        assert item.preview_name == "01_file"

        plans = RenamePlanEngine.generate([item])
        assert plans[0].target_name == "01_file.txt"
        assert plans[0].needs_rename
