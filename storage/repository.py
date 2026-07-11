from __future__ import annotations

from pathlib import Path

from models.rule import Rule
from storage.json_storage import JsonStorage


class RuleRepository:
    """规则仓库 —— 管理内存中的 Rule 列表，通过 JsonStorage 持久化。"""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._rules: list[Rule] = []
        self._storage = JsonStorage()

    # ---------- 持久化 ----------

    def load(self) -> None:
        self._rules = self._storage.load_rules(self._path)
        if not self._rules:
            self._init_defaults()
            self.save()

    def save(self) -> None:
        self._storage.save_rules(self._path, self._rules)

    # ---------- 查询 ----------

    def all_rules(self) -> list[Rule]:
        return list(self._rules)

    def find(self, rule_id: str) -> Rule | None:
        for r in self._rules:
            if r.id == rule_id:
                return r
        return None

    # ---------- 修改 ----------

    def add(self, rule: Rule) -> None:
        self._rules.append(rule)

    def update(self, rule: Rule) -> None:
        for i, r in enumerate(self._rules):
            if r.id == rule.id:
                self._rules[i] = rule
                return

    def remove(self, rule_id: str) -> None:
        self._rules = [r for r in self._rules if r.id != rule_id]

    # ---------- 内部 ----------

    def _init_defaults(self) -> None:
        self._rules = [
            Rule(
                id="default",
                name="默认规则",
                description="系统默认规则",
                steps=[],
            ),
        ]
