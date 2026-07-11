from __future__ import annotations

from engine.rule_engine import RuleEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rule import Rule


class PreviewEngine:
    """预览引擎 —— 对全部 FileItem 调用 RuleEngine，写入 preview_name。"""

    @staticmethod
    def generate_preview(items: list[FileItem], rule: Rule) -> None:
        total = len(items)
        for i, item in enumerate(items):
            if item.item_type == ItemType.FILE:
                ctx = {"index": i + 1, "count": total}
                item.preview_name = RuleEngine.apply(item, rule, ctx)
            else:
                item.preview_name = None
