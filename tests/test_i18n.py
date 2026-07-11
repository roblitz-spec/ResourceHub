from __future__ import annotations

from i18n.translator import Translator


class TestI18n:
    """i18n Translator 单元测试。"""

    def test_default_zh_cn(self) -> None:
        t = Translator()
        assert t.current_language == "zh_CN"
        assert t.translate("menu.tools") == "工具"
        assert t.translate("btn.rename") == "执行重命名"
        assert t.translate("msg.no_undo") == "没有可撤销的操作。"

    def test_switch_to_en_us(self) -> None:
        t = Translator()
        t.set_language("en_US")
        assert t.current_language == "en_US"
        assert t.translate("menu.tools") == "Tools"
        assert t.translate("btn.rename") == "Execute Rename"
        assert t.translate("msg.no_undo") == "No operation to undo."

    def test_unknown_key_returns_itself(self) -> None:
        t = Translator()
        assert t.translate("nonexistent.key") == "nonexistent.key"
