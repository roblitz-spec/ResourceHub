from __future__ import annotations

import json
from pathlib import Path

from models.rule import Rule
from models.rule_step import RuleStep

_CURRENT_VERSION = 1


class JsonStorage:
    """Rule 的 JSON 文件读写 —— 纯序列化，无业务逻辑。"""

    @staticmethod
    def load_rules(path: Path) -> list[Rule]:
        if not path.is_file():
            return []

        data = json.loads(path.read_text(encoding="utf-8"))

        rules: list[Rule] = []
        for item in data.get("rules", []):
            steps = [
                RuleStep(type=s["type"], parameters=s.get("parameters", {}))
                for s in item.get("steps", [])
            ]
            rules.append(Rule(
                id=item["id"],
                name=item["name"],
                description=item.get("description", ""),
                steps=steps,
                pinned=item.get("pinned", False),  # 向后兼容：旧数据无此字段
            ))
        return rules

    @staticmethod
    def save_rules(path: Path, rules: list[Rule]) -> None:
        data = {
            "version": _CURRENT_VERSION,
            "rules": [
                {
                    "id": r.id,
                    "name": r.name,
                    "description": r.description,
                    "pinned": r.pinned,
                    "steps": [
                        {"type": s.type, "parameters": s.parameters}
                        for s in r.steps
                    ],
                }
                for r in rules
            ],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4, default=str),
            encoding="utf-8",
        )
