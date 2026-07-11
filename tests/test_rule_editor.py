from __future__ import annotations

import tempfile
from pathlib import Path

from models.rule import Rule
from models.rule_step import RuleStep
from storage.json_storage import JsonStorage
from storage.repository import RuleRepository


class TestRuleEditor:
    """RuleStep 编辑 & 持久化测试。"""

    def test_rule_with_steps_persists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            repo = RuleRepository(p)
            repo.load()

            rule = Rule(id="r1", name="测试", steps=[
                RuleStep(type="replace", parameters={"from": "_", "to": " "}),
                RuleStep(type="add_prefix", parameters={"text": "[HD]"}),
            ])
            repo.add(rule)
            repo.save()

            repo2 = RuleRepository(p)
            repo2.load()
            r = repo2.find("r1")
            assert r is not None
            assert len(r.steps) == 2
            assert r.steps[0].type == "replace"
            assert r.steps[0].parameters["from"] == "_"
            assert r.steps[1].type == "add_prefix"
            assert r.steps[1].parameters["text"] == "[HD]"

    def test_step_order_persists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            repo = RuleRepository(p)
            repo.load()

            rule = Rule(id="r1", name="顺序", steps=[
                RuleStep(type="add_prefix", parameters={"text": "A"}),
                RuleStep(type="replace", parameters={"from": "x", "to": "y"}),
            ])
            repo.add(rule)
            repo.save()

            repo2 = RuleRepository(p)
            repo2.load()
            r = repo2.find("r1")
            assert r.steps[0].type == "add_prefix"
            assert r.steps[1].type == "replace"

    def test_json_roundtrip_with_steps(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rules.json"
            rules = [
                Rule(id="r1", name="R1", steps=[
                    RuleStep(type="replace", parameters={"from": "_", "to": " "}),
                ]),
            ]
            JsonStorage.save_rules(p, rules)
            loaded = JsonStorage.load_rules(p)
            assert len(loaded) == 1
            assert len(loaded[0].steps) == 1
            assert loaded[0].steps[0].parameters["from"] == "_"
