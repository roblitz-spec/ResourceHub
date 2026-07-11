from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from engine.operation_logger import OperationLogger
from engine.rename_engine import RenameEngine
from models.rename_plan import RenamePlan
from models.rename_result import RenameResult


class RenameWorker(QThread):
    """后台重命名线程 —— 在非 UI 线程逐项执行 rename 并报告进度。"""

    finished_with_result = Signal(list)
    progress_changed = Signal(int, int)

    def __init__(
        self,
        plans: list[RenamePlan],
        logger: OperationLogger | None = None,
        parent: QThread | None = None,
    ) -> None:
        super().__init__(parent)
        self._plans = plans
        self._logger = logger

    def run(self) -> None:
        total = len(self._plans)
        results: list[RenameResult] = []
        try:
            for i, plan in enumerate(self._plans):
                batch_result = RenameEngine.rename(
                    [plan], self._logger,
                )
                results.extend(batch_result)
                self.progress_changed.emit(i + 1, total)
        except Exception:
            pass
        self.finished_with_result.emit(results)
