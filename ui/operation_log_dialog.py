from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from engine.operation_logger import OperationLogger
from i18n.translator import Translator
from models.operation_record import OperationRecord

_COLUMNS = ["时间", "源文件", "目标文件", "结果", "消息"]


class OperationLogDialog(QDialog):
    """操作日志查看器 —— 只读显示 OperationLogger 中的所有记录。"""

    def __init__(
        self, logger: OperationLogger,
        translator: Translator | None = None,
        parent: QDialog | None = None,
    ) -> None:
        super().__init__(parent)
        self._logger = logger
        self._tr = translator or Translator()

        self.setWindowTitle("操作日志")
        self.resize(800, 400)

        layout = QVBoxLayout(self)

        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self._table)

        # 按钮
        export_btn = QPushButton(self._tr.translate("btn.export"))
        export_btn.clicked.connect(self._on_export)

        clear_btn = QPushButton(self._tr.translate("btn.clear_log"))
        clear_btn.clicked.connect(self._on_clear)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.addButton(export_btn, QDialogButtonBox.ActionRole)
        buttons.addButton(clear_btn, QDialogButtonBox.ActionRole)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh()

    # ---------- 内部 ----------

    @staticmethod
    def _result_label(record: OperationRecord) -> str:
        if not record.success:
            return "失败"
        if record.message == "已跳过":
            return "跳过"
        return "成功"

    def _refresh(self) -> None:
        records = self._logger.records()
        self._table.setRowCount(len(records))
        for row, rec in enumerate(records):
            self._table.setItem(row, 0, QTableWidgetItem(
                rec.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            ))
            self._table.setItem(row, 1, QTableWidgetItem(str(rec.source)))
            self._table.setItem(row, 2, QTableWidgetItem(str(rec.target)))
            self._table.setItem(row, 3, QTableWidgetItem(self._result_label(rec)))
            self._table.setItem(row, 4, QTableWidgetItem(rec.message))

    def _on_clear(self) -> None:
        self._logger.clear()
        self._refresh()

    # ---------- 导出 ----------

    def _on_export(self) -> None:
        records = self._logger.records()
        if not records:
            QMessageBox.information(self, "提示", self._tr.translate("msg.no_export"))
            return

        path_str, _filter = QFileDialog.getSaveFileName(
            self, "导出日志", "",
            "CSV (*.csv);;TXT (*.txt)",
        )
        if not path_str:
            return

        path = Path(path_str)
        try:
            if path.suffix.lower() == ".csv":
                self._export_csv(records, path)
            else:
                self._export_txt(records, path)
        except OSError:
            QMessageBox.warning(self, "导出失败", self._tr.translate("msg.export_failed"))

    @staticmethod
    def _export_csv(records: list[OperationRecord], path: Path) -> None:
        lines = ["time,source,target,result,message"]
        for rec in records:
            result = OperationLogDialog._result_label(rec)
            lines.append(
                f"{rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')},"
                f'"{rec.source}","{rec.target}",{result},"{rec.message}"'
            )
        path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _export_txt(records: list[OperationRecord], path: Path) -> None:
        lines: list[str] = []
        for rec in records:
            result = OperationLogDialog._result_label(rec)
            lines.append(
                f"[{rec.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{rec.source} → {rec.target} | {result} | {rec.message}"
            )
        path.write_text("\n".join(lines), encoding="utf-8")
