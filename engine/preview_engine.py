from __future__ import annotations

from engine.rule_engine import RuleEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rule import Rule


class PreviewEngine:
    """预览引擎 —— 对全部 FileItem 调用 RuleEngine，写入 preview_name。"""

    @staticmethod
    def generate_preview(items: list[FileItem], rule: Rule) -> None:
        file_index = 0
        for item in items:
            if item.item_type == ItemType.FILE:
                file_index += 1
                ctx: dict = {"index": file_index, "count": len(items)}
                try:
                    st = item.full_path.stat()
                    ctx["timestamps"] = {
                        "modified": st.st_mtime,
                        "created": st.st_ctime,
                    }
                except OSError:
                    pass
                item.preview_name = RuleEngine.apply(item, rule, ctx)
            else:
                item.preview_name = None
