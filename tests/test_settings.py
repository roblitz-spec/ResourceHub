from __future__ import annotations

import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings

from config.settings import Settings
from models.rename_policy import RenamePolicy


def _make_settings(path: Path) -> Settings:
    s = Settings()
    s._init_qsettings(QSettings(str(path), QSettings.IniFormat))
    return s


class TestSettings:
    """Settings 单元测试（使用临时 QSettings 文件）。"""

    def test_default_is_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            s = _make_settings(Path(td) / "test.ini")
            assert s.get_rename_policy() == RenamePolicy.FAIL

    def test_save_and_load_skip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.ini"
            s = _make_settings(p)
            s.set_rename_policy(RenamePolicy.SKIP)

            s2 = _make_settings(p)
            assert s2.get_rename_policy() == RenamePolicy.SKIP

    def test_save_and_load_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.ini"
            s = _make_settings(p)
            s.set_rename_policy(RenamePolicy.OVERWRITE)

            s2 = _make_settings(p)
            assert s2.get_rename_policy() == RenamePolicy.OVERWRITE

    def test_invalid_value_falls_back(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.ini"
            # 直接写入非法值到 QSettings
            qs = QSettings(str(p), QSettings.IniFormat)
            qs.setValue("rename/policy", "INVALID")

            s = _make_settings(p)
            assert s.get_rename_policy() == RenamePolicy.FAIL
