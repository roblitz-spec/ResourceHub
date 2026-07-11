from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class TestBuildConfig:
    """构建配置验证测试。"""

    def test_spec_exists(self) -> None:
        assert (ROOT / "build.spec").is_file()

    def test_translations_in_spec(self) -> None:
        content = (ROOT / "build.spec").read_text()
        assert "translations" in content

    def test_entry_main_exists(self) -> None:
        assert (ROOT / "main.py").is_file()

    def test_requirements_has_pyinstaller(self) -> None:
        content = (ROOT / "requirements.txt").read_text()
        # PyInstaller is required for build
        assert "PyInstaller" in content or "pyinstaller" in content.lower()
