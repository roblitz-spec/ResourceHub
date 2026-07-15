from __future__ import annotations

from dataclasses import dataclass

from models.rule import Rule


@dataclass
class RuleAnalysis:
    """Rule 对 Context 的依赖声明。

    在 Preview 循环外调用 analyze() 一次，结果在循环中复用。
    """

    uses_index: bool = False
    uses_metadata: bool = False

    @staticmethod
    def analyze(rule: Rule) -> RuleAnalysis:
        result = RuleAnalysis()
        for step in rule.steps:
            if step.type == "number":
                result.uses_index = True
            elif step.type == "date":
                result.uses_metadata = True
        return result
