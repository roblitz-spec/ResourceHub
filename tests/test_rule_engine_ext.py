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

    def test_insert_at_len_clamped(self) -> None:
        """at_index > len → 自动追加到末尾。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "Z", "at_index": "999"}),
        ])
        assert RuleEngine.apply(_file_item("ab"), rule) == "abZ"

    def test_insert_neg2_also_clamped(self) -> None:
        """at_index = -2 也 clamp 到末尾。"""
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "Z", "at_index": "-2"}),
        ])
        assert RuleEngine.apply(_file_item("ab"), rule) == "abZ"

    def test_insert_save_load(self) -> None:
        """Insert Rule 保存/加载 text + at_index 恢复。"""
        import tempfile
        from pathlib import Path
        from storage.repository import RuleRepository

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            repo = RuleRepository(p); repo.load()
            repo.add(Rule(id="r1", name="插入", steps=[
                RuleStep(type="insert", parameters={"text": "_v2", "at_index": "5"}),
            ]))
            repo.save()
            repo2 = RuleRepository(p); repo2.load()
            r = repo2.find("r1")
            assert r.steps[0].parameters["text"] == "_v2"
            assert r.steps[0].parameters["at_index"] == "5"

    def test_insert_preview_rename_consistency(self) -> None:
        """Insert: Preview → RenamePlan → target_name 一致。"""
        item = _file_item("file", ".txt")
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="insert", parameters={"text": "_v2", "at_index": "4"}),
        ])
        PreviewEngine.generate_preview([item], rule)
        assert item.preview_name == "file_v2"
        plans = RenamePlanEngine.generate([item])
        assert plans[0].target_name == "file_v2.txt"
        assert plans[0].needs_rename


class TestDateRule:
    """Date RuleStep 测试。"""

    TS = 1720134000.0  # 2024-07-04T23:00:00 UTC

    def _ctx(self, source="modified"):
        return {"timestamps": {source: self.TS}}

    def test_default_prefix(self) -> None:
        rule = Rule(id="r", name="r", steps=[RuleStep(type="date", parameters={})])
        result = RuleEngine.apply(_file_item("photo"), rule, self._ctx())
        assert result.startswith("2024-07-04_photo")

    def test_suffix(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"position": "suffix"}),
        ])
        result = RuleEngine.apply(_file_item("photo"), rule, self._ctx())
        assert result.endswith("_2024-07-04")

    def test_custom_format(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"format": "%Y%m%d_%H%M"}),
        ])
        result = RuleEngine.apply(_file_item("photo"), rule, self._ctx())
        assert result.startswith("20240704")

    def test_custom_separator(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"separator": "-"}),
        ])
        result = RuleEngine.apply(_file_item("photo"), rule, self._ctx())
        assert result.startswith("2024-07-04-photo")

    def test_empty_separator(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"separator": ""}),
        ])
        result = RuleEngine.apply(_file_item("photo"), rule, self._ctx())
        assert result.startswith("2024-07-04photo")

    def test_modified_source(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"source": "modified"}),
        ])
        result = RuleEngine.apply(_file_item("f"), rule, self._ctx("modified"))
        assert "2024-07-04" in result

    def test_unknown_source_returns_original(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"source": "exif"}),
        ])
        result = RuleEngine.apply(_file_item("photo"), rule, self._ctx())
        assert result == "photo"  # exif not found → original

    def test_missing_context_returns_original(self) -> None:
        rule = Rule(id="r", name="r", steps=[RuleStep(type="date", parameters={})])
        result = RuleEngine.apply(_file_item("photo"), rule)
        assert result == "photo"  # no context → original

    def test_date_then_prefix(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"separator": ""}),
            RuleStep(type="add_prefix", parameters={"text": "[OK]"}),
        ])
        result = RuleEngine.apply(_file_item("f"), rule, self._ctx())
        assert result == "[OK]2024-07-04f"

    def test_prefix_then_date(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="add_prefix", parameters={"text": "[OK]"}),
            RuleStep(type="date", parameters={"separator": ""}),
        ])
        result = RuleEngine.apply(_file_item("f"), rule, self._ctx())
        assert result == "2024-07-04[OK]f"

    def test_date_then_number(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="date", parameters={"separator": ""}),
            RuleStep(type="number", parameters={"padding": "2"}),
        ])
        result = RuleEngine.apply(_file_item("f"), rule, {**self._ctx(), "index": 1})
        assert result == "01_2024-07-04f"

    def test_number_then_date(self) -> None:
        rule = Rule(id="r", name="r", steps=[
            RuleStep(type="number", parameters={"padding": "2"}),
            RuleStep(type="date", parameters={"separator": ""}),
        ])
        result = RuleEngine.apply(_file_item("f"), rule, {**self._ctx(), "index": 1})
        assert result == "2024-07-0401_f"

    def test_preview_consistency(self) -> None:
        """Date Rule: Preview ↔ RenamePlan 一致。"""
        import os as _os
        import tempfile, shutil
        from pathlib import Path
        d = Path(tempfile.mkdtemp())
        p = d / "photo.txt"; p.write_text("x")
        _os.utime(p, (self.TS, self.TS))
        item = FileItem(full_path=p, original_name="photo.txt", base_name="photo", extension=".txt", item_type=ItemType.FILE)
        rule = Rule(id="r", name="r", steps=[RuleStep(type="date", parameters={})])
        PreviewEngine.generate_preview([item], rule)
        assert "2024-07-04" in item.preview_name
        plans = RenamePlanEngine.generate([item])
        assert "2024-07-04" in plans[0].target_name
        shutil.rmtree(d)


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
