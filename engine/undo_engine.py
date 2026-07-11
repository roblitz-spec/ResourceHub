from __future__ import annotations

from typing import TYPE_CHECKING

from models.rename_result import RenameResult

if TYPE_CHECKING:
    from engine.operation_logger import OperationLogger


class UndoEngine:
    """撤销引擎 —— 基于 OperationLogger 逆序撤销最近一次重命名。"""

    @staticmethod
    def undo(logger: OperationLogger) -> list[RenameResult]:
        results: list[RenameResult] = []

        for record in reversed(logger.records()):
            # 跳过：失败 / 已跳过 / 目录（source == target）
            if not record.success:
                continue
            if record.message == "已跳过":
                continue
            if record.source == record.target:
                continue

            try:
                record.target.rename(record.source)
                results.append(RenameResult(
                    source=record.target, target=record.source, success=True,
                ))
            except Exception as exc:
                results.append(RenameResult(
                    source=record.target, target=record.source,
                    success=False, message=str(exc),
                ))

        logger.clear()
        return results
