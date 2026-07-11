from __future__ import annotations

import tempfile
from pathlib import Path

from engine.preview_engine import PreviewEngine
from engine.rename_engine import RenameEngine
from engine.rename_plan_engine import RenamePlanEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rule import Rule
from models.rule_step import RuleStep
from scanner.scanner import Scanner
from validator.validator import Validator


class TestRenameE2E:
    """端到端重命名回归测试。"""

    def test_single_file_replace_a_to_b(self) -> None:
        """A.txt → Replace A→B → B.txt"""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "A.txt").write_text("hello")

            # 扫描
            items = Scanner.scan(root)
            assert len(items) == 1
            assert items[0].original_name == "A.txt"

            # 预览
            rule = Rule(id="r", name="r", steps=[
                RuleStep(type="replace", parameters={"from": "A", "to": "B"}),
            ])
            PreviewEngine.generate_preview(items, rule)
            assert items[0].preview_name == "B"

            # 校验
            results = Validator.validate(items)
            assert all(r.is_valid for r in results)

            # 执行
            rename_results = RenameEngine.rename(RenamePlanEngine.generate(items))
            assert rename_results[0].success
            assert not (root / "A.txt").exists()
            assert (root / "B.txt").exists()
            assert (root / "B.txt").read_text() == "hello"
