from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

_TRANSLATIONS_DIR = Path(__file__).resolve().parent.parent / "translations"


class Translator:
    """国际化翻译器 —— 从 Qt Linguist .ts 文件加载翻译。"""

    def __init__(self, default_lang: str = "zh_CN") -> None:
        self._entries: dict[str, str] = {}
        self._current_lang = ""
        self.set_language(default_lang)

    def set_language(self, lang: str) -> None:
        self._current_lang = lang
        self._entries.clear()
        path = _TRANSLATIONS_DIR / f"{lang}.ts"
        if not path.is_file():
            return
        tree = ET.parse(str(path))
        root = tree.getroot()
        for message in root.iter("message"):
            source = message.find("source")
            translation = message.find("translation")
            if source is not None and translation is not None and translation.text:
                self._entries[source.text or ""] = translation.text

    def translate(self, key: str) -> str:
        return self._entries.get(key, key)

    @property
    def current_language(self) -> str:
        return self._current_lang
