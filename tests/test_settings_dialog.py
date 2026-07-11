from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from config.settings import Settings
from models.rename_policy import RenamePolicy
from ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def _make_settings(path: Path) -> Settings:
    s = Settings()
    s._init_qsettings(QSettings(str(path), QSettings.IniFormat))
    return s


class TestSettingsDialog:
    """SettingsDialog 单元测试。"""

    def test_shows_current_policy(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            s = _make_settings(Path(td) / "test.ini")
            s.set_rename_policy(RenamePolicy.SKIP)

            dialog = SettingsDialog(s)
            idx = dialog._policy_combo.currentIndex()
            assert dialog._policy_combo.itemData(idx) == RenamePolicy.SKIP

    def test_ok_saves(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.ini"
            s = _make_settings(p)
            s.set_rename_policy(RenamePolicy.FAIL)

            dialog = SettingsDialog(s)
            dialog._policy_combo.setCurrentIndex(2)  # OVERWRITE
            dialog._on_accept()

            s2 = _make_settings(p)
            assert s2.get_rename_policy() == RenamePolicy.OVERWRITE

    def test_cancel_does_not_save(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.ini"
            s = _make_settings(p)
            s.set_rename_policy(RenamePolicy.FAIL)

            dialog = SettingsDialog(s)
            dialog._policy_combo.setCurrentIndex(1)  # SKIP
            dialog.reject()

            s2 = _make_settings(p)
            assert s2.get_rename_policy() == RenamePolicy.FAIL

    def test_reopen_shows_saved(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.ini"
            s = _make_settings(p)
            s.set_rename_policy(RenamePolicy.OVERWRITE)

            dialog1 = SettingsDialog(s)
            idx1 = dialog1._policy_combo.currentIndex()
            assert dialog1._policy_combo.itemData(idx1) == RenamePolicy.OVERWRITE

            # 模拟确定，实际调用 _on_accept
            dialog1._policy_combo.setCurrentIndex(0)  # FAIL
            dialog1._on_accept()

            s2 = _make_settings(p)
            dialog2 = SettingsDialog(s2)
            idx2 = dialog2._policy_combo.currentIndex()
            assert dialog2._policy_combo.itemData(idx2) == RenamePolicy.FAIL
