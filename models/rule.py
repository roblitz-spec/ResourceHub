from __future__ import annotations

from dataclasses import dataclass, field

from models.rule_step import RuleStep


@dataclass
class Rule:
    """重命名规则。"""

    id: str
    name: str
    description: str = ""
    steps: list[RuleStep] = field(default_factory=list)
