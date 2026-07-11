#!/usr/bin/env python3
"""一键构建脚本 —— 清理旧输出，调用 PyInstaller 打包。"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "ResourceHub"
BUILD = ROOT / "build" / "ResourceHub"
SPEC = ROOT / "build.spec"


def clean() -> None:
    for p in (BUILD, DIST):
        if p.exists():
            shutil.rmtree(p)
    for f in ROOT.glob("*.spec"):
        if f.name != "build.spec":
            f.unlink()


def build() -> None:
    clean()
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(SPEC), "--distpath", str(ROOT / "dist")],
        cwd=str(ROOT),
    )
    if result.returncode != 0:
        print("构建失败。", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"\n构建成功 → {DIST}")


if __name__ == "__main__":
    build()
