from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from engine.rename_plan_engine import RenamePlanEngine
from models.enums import ItemType
from models.file_item import FileItem
from workers.rename_worker import RenameWorker


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


def _file(path: Path, preview: str) -> FileItem:
    return FileItem(
        full_path=path, original_name=path.name,
        base_name=path.stem, extension=path.suffix,
        item_type=ItemType.FILE, preview_name=preview,
    )


def _plan(item: FileItem):
    return RenamePlanEngine.generate([item])[0]


class TestProgressSignal:
    """RenameWorker progress_changed 信号测试。"""

    def test_progress_emission_count(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            items = []
            for i in range(3):
                p = root / f"file_{i}.txt"
                p.write_text(str(i))
                items.append(_file(p, f"renamed_{i}"))

            progress_values: list[tuple[int, int]] = []
            worker = RenameWorker([_plan(i) for i in items])
            worker.progress_changed.connect(
                lambda c, t: progress_values.append((c, t)),
                Qt.DirectConnection,
            )
            worker.start()
            worker.wait()

            assert len(progress_values) == 3
            assert progress_values[-1] == (3, 3)

    def test_current_equals_total_at_end(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            items: list[FileItem] = []
            for i in range(2):
                p = root / f"f{i}.txt"
                p.write_text("x")
                items.append(_file(p, f"r{i}"))

            last: list[tuple[int, int]] = []
            worker = RenameWorker([_plan(i) for i in items])
            worker.progress_changed.connect(
                lambda c, t: last.append((c, t)),
                Qt.DirectConnection,
            )
            worker.start()
            worker.wait()

            assert last[-1][0] == last[-1][1]

    def test_finished_signal(self, qapp: QApplication) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            src = root / "a.txt"; src.write_text("ok")
            captured: list = []

            worker = RenameWorker([_plan(_file(src, "b"))])
            worker.finished_with_result.connect(
                captured.extend, Qt.DirectConnection,
            )
            worker.start()
            worker.wait()

            assert len(captured) == 1
            assert captured[0].success
