from __future__ import annotations

from PySide6.QtCore import QSettings

from models.rename_policy import RenamePolicy

_ORGANIZATION = "ResourceHub"
_APPLICATION = "ResourceHub"
_KEY_POLICY = "rename/policy"
_KEY_LAST_RULE = "rule/last_selected"


class Settings:
    """应用设置 —— 基于 QSettings，目前仅管理默认重命名策略。"""

    def __init__(self) -> None:
        self._qsettings = QSettings(_ORGANIZATION, _APPLICATION)

    def _init_qsettings(self, qsettings: QSettings) -> None:
        """仅供测试注入自定义 QSettings 实例。"""
        self._qsettings = qsettings

    def get_rename_policy(self) -> RenamePolicy:
        raw = self._qsettings.value(_KEY_POLICY)
        if isinstance(raw, str):
            try:
                return RenamePolicy(raw)
            except ValueError:
                pass
        return RenamePolicy.FAIL

    def set_rename_policy(self, policy: RenamePolicy) -> None:
        self._qsettings.setValue(_KEY_POLICY, policy.value)

    def get_last_rule_id(self) -> str | None:
        raw = self._qsettings.value(_KEY_LAST_RULE)
        return raw if isinstance(raw, str) else None

    def set_last_rule_id(self, rule_id: str) -> None:
        self._qsettings.setValue(_KEY_LAST_RULE, rule_id)
