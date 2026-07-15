from __future__ import annotations

from engine.metadata_provider import MetadataProvider
from engine.rule_analysis import RuleAnalysis
from engine.rule_engine import RuleEngine
from models.file_item import FileItem
from models.rule import Rule


class PreviewEngine:
    """预览引擎 —— 对全部 FileItem 调用 RuleEngine，写入 preview_name。"""

    @staticmethod
    def generate_preview(items: list[FileItem], rule: Rule) -> None:
        analysis = RuleAnalysis.analyze(rule)

        file_index = 0
        for item in items:
            ctx: dict = {}
            if analysis.uses_index:
                file_index += 1
                ctx["index"] = file_index
            if analysis.uses_metadata:
                ctx["metadata"] = MetadataProvider(item.full_path)

            item.preview_name = RuleEngine.apply(item, rule, ctx)
