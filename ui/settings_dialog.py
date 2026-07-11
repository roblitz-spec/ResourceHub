from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
)

from config.settings import Settings
from models.rename_policy import RenamePolicy

_POLICY_OPTIONS: list[tuple[str, RenamePolicy]] = [
    ("失败（FAIL）", RenamePolicy.FAIL),
    ("跳过（SKIP）", RenamePolicy.SKIP),
    ("覆盖（OVERWRITE）", RenamePolicy.OVERWRITE),
]


class SettingsDialog(QDialog):
    """设置对话框 —— 当前仅允许修改默认重命名冲突策略。"""

    def __init__(self, settings: Settings, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self._settings = settings

        self.setWindowTitle("设置")

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._policy_combo = QComboBox()
        for label, policy in _POLICY_OPTIONS:
            self._policy_combo.addItem(label, policy)
        form.addRow("目标文件冲突时：", self._policy_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._load_current()

    def _load_current(self) -> None:
        current = self._settings.get_rename_policy()
        for i in range(self._policy_combo.count()):
            if self._policy_combo.itemData(i) == current:
                self._policy_combo.setCurrentIndex(i)
                return

    def _on_accept(self) -> None:
        policy = self._policy_combo.currentData()
        if isinstance(policy, RenamePolicy):
            self._settings.set_rename_policy(policy)
        self.accept()
