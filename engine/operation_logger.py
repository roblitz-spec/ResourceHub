from __future__ import annotations

from datetime import datetime

from models.operation_record import OperationRecord
from models.rename_result import RenameResult


class OperationLogger:
    """执行日志 —— 仅内存存储，不写文件。"""

    def __init__(self) -> None:
        self._records: list[OperationRecord] = []

    def record(self, result: RenameResult) -> None:
        self._records.append(OperationRecord(
            timestamp=datetime.now(),
            source=result.source,
            target=result.target,
            success=result.success,
            message=result.message,
        ))

    def records(self) -> list[OperationRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()
