from __future__ import annotations

import re

from models.file_item import FileItem
from models.rule import Rule


def _handle_replace(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    return text.replace(str(params["from"]), str(params["to"]))


def _handle_remove_text(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    return text.replace(str(params["text"]), "")


def _handle_add_prefix(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    return str(params["text"]) + text


def _handle_regex_replace(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    pattern = str(params["pattern"])
    repl = str(params.get("replacement", ""))
    flags_str = str(params.get("flags", ""))
    flags = 0
    for ch in flags_str:
        flags |= getattr(re, ch.upper(), 0)
    return re.sub(pattern, repl, text, flags=flags)


def _handle_case(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    mode = str(params.get("mode", "lower"))
    if mode == "upper":
        return text.upper()
    elif mode == "lower":
        return text.lower()
    elif mode == "title":
        return text.title()
    elif mode == "capitalize":
        return text.capitalize()
    return text


def _handle_trim(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    mode = str(params.get("mode", "both"))
    if mode == "left":
        return text.lstrip()
    elif mode == "right":
        return text.rstrip()
    return text.strip()


def _handle_date(text: str, params: dict[str, object], ctx: dict | None = None) -> str:
    from datetime import datetime

    source = str(params.get("source", "modified"))
    fmt = str(params.get("format", "%Y-%m-%d"))
    pos = str(params.get("position", "prefix"))
    sep = str(params.get("separator", "_"))

    ts = None
    provider = (ctx or {}).get("metadata")
    if provider is not None:
        ts = provider.modified if source == "modified" else provider.created

    if ts is None:
        return text  # 纯函数：无时间戳 → 返回原名

    date_str = datetime.fromtimestamp(ts).strftime(fmt)
    if pos == "suffix":
        return f"{text}{sep}{date_str}"
    return f"{date_str}{sep}{text}"


def _handle_add_suffix(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    return text + str(params["text"])


def _handle_insert(text: str, params: dict[str, object], _ctx: dict | None = None) -> str:
    insert_text = str(params.get("text", ""))
    at_idx = int(str(params.get("at_index", "0")))
    if at_idx < 0 or at_idx > len(text):
        at_idx = len(text)
    return text[:at_idx] + insert_text + text[at_idx:]


def _handle_number(text: str, params: dict[str, object], ctx: dict | None = None) -> str:
    idx = (ctx or {}).get("index", 1)
    start = int(str(params.get("start", "1")))
    step = int(str(params.get("step", "1")))
    padding = int(str(params.get("padding", "3")))
    position = str(params.get("position", "prefix"))

    num = start + (idx - 1) * step
    formatted = str(num).zfill(padding) if padding > 0 else str(num)

    if position == "suffix":
        return f"{text}_{formatted}"
    return f"{formatted}_{text}"


_HANDLERS: dict[str, object] = {
    "replace": _handle_replace,
    "remove_text": _handle_remove_text,
    "add_prefix": _handle_add_prefix,
    "regex_replace": _handle_regex_replace,
    "case": _handle_case,
    "trim": _handle_trim,
    "number": _handle_number,
    "insert": _handle_insert,
    "date": _handle_date,
    "add_suffix": _handle_add_suffix,
}


class RuleEngine:
    """规则引擎 —— 按 RuleStep 列表顺序逐条处理 base_name，返回新名称。

    apply() 接受可选 context 字典（如 {"index": 1, "count": 10}），
    由调用方提供编号上下文。无 context 时所有 handler 保持原行为。
    """

    @staticmethod
    def apply(file_item: FileItem, rule: Rule, context: dict | None = None) -> str:
        result = file_item.base_name
        for step in rule.steps:
            handler = _HANDLERS.get(step.type)
            if handler is not None:
                try:
                    result = handler(result, step.parameters, context)  # type: ignore[operator]
                except re.error:
                    pass  # 非法正则 → 保持原名
        return result
