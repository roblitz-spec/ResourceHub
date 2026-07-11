from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuleStep:
    """重命名规则中的一个步骤。"""

    type: str
    parameters: dict[str, object] = field(default_factory=dict)
