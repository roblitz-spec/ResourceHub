from __future__ import annotations

import os
import time
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from models.enums import ItemType
from models.file_item import FileItem

_DEBUG = os.environ.get("RESOURCEHUB_DEBUG", "") == "1"

_COLUMNS = ["类型", "原名称", "扩展名", "完整路径", "预览名称"]

_TYPE_LABELS: dict[ItemType, str] = {
    ItemType.FILE: "文件",
    ItemType.DIRECTORY: "文件夹",
}

_ROLE_NAMES: dict[int, str] = {
    Qt.DisplayRole: "DisplayRole",
    Qt.DecorationRole: "DecorationRole",
    Qt.EditRole: "EditRole",
    Qt.ToolTipRole: "ToolTipRole",
    Qt.StatusTipRole: "StatusTipRole",
    Qt.WhatsThisRole: "WhatsThisRole",
    Qt.FontRole: "FontRole",
    Qt.TextAlignmentRole: "TextAlignmentRole",
    Qt.BackgroundRole: "BackgroundRole",
    Qt.ForegroundRole: "ForegroundRole",
    Qt.CheckStateRole: "CheckStateRole",
    Qt.SizeHintRole: "SizeHintRole",
    Qt.UserRole: "UserRole",
}


class FileTableModel(QAbstractTableModel):
    """文件列表的 Qt Model/View 模型。"""

    def __init__(self, parent: QAbstractTableModel | None = None) -> None:
        super().__init__(parent)
        self._items: list[FileItem] = []
        self._role_calls: dict[str, int] = defaultdict(int)
        self._role_time: dict[str, float] = defaultdict(float)
        self._data_was_called = False

    # ---------- QAbstractTableModel 接口 ----------

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if _DEBUG:
            self._data_was_called = True
            t0 = time.perf_counter()

        if not index.isValid():
            if _DEBUG:
                self._record_role(role, t0)
            return None

        if role != Qt.DisplayRole:
            if _DEBUG:
                self._record_role(role, t0)
            return None

        item = self._items[index.row()]
        col = index.column()
        result: str | None
        if col == 0:
            result = _TYPE_LABELS[item.item_type]
        elif col == 1:
            result = item.original_name
        elif col == 2:
            result = item.extension
        elif col == 3:
            result = str(item.full_path)
        elif col == 4:
            result = item.preview_name or ""
        else:
            result = None

        if _DEBUG:
            self._record_role(role, t0)
        return result

    def _record_role(self, role: int, t0: float) -> None:
        name = _ROLE_NAMES.get(role, f"Role({role})")
        self._role_calls[name] += 1
        self._role_time[name] += time.perf_counter() - t0

    def dump_role_stats(self) -> None:
        if not _DEBUG:
            return
        if not self._data_was_called:
            print("[Model Profiling] Model.data() was never called.", flush=True)
            return
        print("[Model Profiling] data() role stats:", flush=True)
        print(f"  {'Role':<22s} {'calls':>8s}  {'total':>10s}  {'avg':>10s}", flush=True)
        print(f"  {'-'*22}  {'-'*8}  {'-'*10}  {'-'*10}", flush=True)
        total_calls = 0
        total_time = 0.0
        for name in sorted(self._role_calls):
            c = self._role_calls[name]
            t = self._role_time[name]
            total_calls += c
            total_time += t
            avg_us = (t / c * 1_000_000) if c else 0
            print(f"  {name:<22s} {c:>8d}  {t*1000:>8.1f} ms  {avg_us:>8.1f} µs", flush=True)
        print(f"  {'-'*22}  {'-'*8}  {'-'*10}  {'-'*10}", flush=True)
        print(f"  {'TOTAL':<22s} {total_calls:>8d}  {total_time*1000:>8.1f} ms", flush=True)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole,
    ) -> str | None:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and 0 <= section < len(_COLUMNS):
            return _COLUMNS[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # ---------- 公开接口 ----------

    def set_items(self, items: list[FileItem]) -> None:
        if _DEBUG:
            t0 = time.perf_counter()
            self._role_calls.clear()
            self._role_time.clear()
            self._data_was_called = False
        self.beginResetModel()
        if _DEBUG:
            t1 = time.perf_counter()
        self._items = items
        if _DEBUG:
            t2 = time.perf_counter()
        self.endResetModel()
        if _DEBUG:
            t3 = time.perf_counter()
            print(f"[Model Profiling] set_items({len(items)} rows):", flush=True)
            print(f"  beginReset:  {(t1-t0)*1000:.1f} ms", flush=True)
            print(f"  data assign: {(t2-t1)*1000:.1f} ms", flush=True)
            print(f"  endReset:    {(t3-t2)*1000:.1f} ms", flush=True)
            print(f"  TOTAL model: {(t3-t0)*1000:.1f} ms", flush=True)

    def refresh_all(self) -> None:
        """仅刷新数据显示，不重建 Model（保持 selection）。"""
        if not self._items:
            return
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(len(self._items) - 1, self.columnCount() - 1),
        )

    def clear(self) -> None:
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

    def item(self, row: int) -> FileItem:
        return self._items[row]

    def items(self) -> list[FileItem]:
        return list(self._items)