from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from engine.preview_engine import PreviewEngine
from models.enums import ItemType
from models.file_item import FileItem
from models.rule import Rule
from scanner.scanner import Scanner

_DEBUG = os.environ.get("RESOURCEHUB_DEBUG", "") == "1"


def _log(msg: str) -> None:
    if not _DEBUG:
        return
    elapsed = time.monotonic() - _log._start
    print(f"[{elapsed:8.3f}] {msg}", flush=True)


_log._start = 0.0  # type: ignore[attr-defined]


class ScanWorker(QThread):
    """后台扫描线程 —— 在非 UI 线程执行目录扫描 + 预览生成。

    扫描结果同时存于 self.items，避免跨线程 Signal 序列化
    大量 FileItem 对象的开销。finished 信号仅携带空列表
    作为通知，接收方从 worker.items 读取实际数据。
    """

    finished = Signal(list)

    def __init__(
        self,
        directory: Path,
        rule: Rule | None = None,
        parent: QThread | None = None,
    ) -> None:
        super().__init__(parent)
        self._directory = directory
        self._rule = rule
        self.items: list[FileItem] = []

    def run(self) -> None:
        t0 = time.monotonic()
        _log._start = t0  # type: ignore[attr-defined]
        _log("Scan requested")

        try:
            t1 = time.monotonic()
            _log("Scanner start")
            items = Scanner.scan(self._directory)
            t2 = time.monotonic()
            dirs = sum(1 for i in items if i.item_type == ItemType.DIRECTORY)
            file_cnt = sum(1 for i in items if i.item_type == ItemType.FILE)
            _log(
                f"Scanner finish  entries={len(items)}  "
                f"dirs={dirs}  files={file_cnt}  "
                f"elapsed={t2 - t1:.3f}s"
            )

            if self._rule is not None:
                t3 = time.monotonic()
                _log("Preview start")
                PreviewEngine.generate_preview(items, self._rule)
                t4 = time.monotonic()
                _log(f"Preview finish  elapsed={t4 - t3:.3f}s")

        except Exception:
            items = []

        self.items = items

        te = time.monotonic()
        _log(f"Scan finished  total elapsed={te - t0:.3f}s")
        _log(f"Worker emit finished  t={te:.3f}")
        _log("-" * 40)

        # 只发空列表作为通知信号；实际数据从 self.items 读取
        self.finished.emit([])
