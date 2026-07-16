from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSortFilterProxyModel
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMenuBar,
    QMessageBox,
    QMainWindow,
    QProgressDialog,
    QPushButton,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from config.settings import Settings
from engine.operation_logger import OperationLogger
from engine.preview_engine import PreviewEngine
from engine.rename_plan_engine import RenamePlanEngine
from engine.undo_engine import UndoEngine
from i18n.translator import Translator
from models.enums import ItemType
from models.file_item import FileItem
from models.rename_plan import RenameAction, RenamePlanStatus
from models.rule import Rule
from storage.repository import RuleRepository
from ui.file_table_model import FileTableModel, SortProxyModel
from ui.operation_log_dialog import OperationLogDialog
from ui.rule_manager_dialog import RuleManagerDialog
from ui.settings_dialog import SettingsDialog
from workers.rename_worker import RenameWorker
from workers.scan_worker import ScanWorker

_DEBUG = os.environ.get("RESOURCEHUB_DEBUG", "") == "1"


def _utime() -> float:
    return time.perf_counter()


class MainWindow(QMainWindow):
    """ResourceHub 主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self._current_dir: Path | None = None
        self._items: list[FileItem] = []
        self._scan_worker: ScanWorker | None = None
        self._rename_worker: RenameWorker | None = None
        self._settings = Settings()
        self._logger = OperationLogger()
        self._tr = Translator()

        # 菜单栏
        self._setup_menu()

        # 规则仓库
        self._repo = RuleRepository(
            Path(__file__).resolve().parent.parent / "config" / "rules.json"
        )
        self._repo.load()

        self.setWindowTitle("ResourceHub v0.1")
        self.resize(1200, 700)
        self.setMinimumSize(1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ---------- 第一行：目录 ----------
        dir_layout = QHBoxLayout()
        dir_label = QLabel("目录：")
        self._dir_edit = QLineEdit()
        self._dir_edit.setReadOnly(True)
        self._dir_edit.setPlaceholderText("请选择目录...")

        self._browse_btn = QPushButton("浏览")
        self._browse_btn.clicked.connect(self._on_browse)

        self._refresh_btn = QPushButton("刷新")
        self._refresh_btn.clicked.connect(self._on_refresh)

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self._dir_edit, stretch=1)
        dir_layout.addWidget(self._browse_btn)
        dir_layout.addWidget(self._refresh_btn)
        main_layout.addLayout(dir_layout)

        # ---------- 第二行：规则 ----------
        rule_layout = QHBoxLayout()
        rule_label = QLabel("规则：")
        self._rule_combo = QComboBox()
        self._rule_combo.currentIndexChanged.connect(self._on_rule_changed)
        for r in self._repo.all_rules():
            self._rule_combo.addItem(r.name, r.id)

        # 恢复上次选中的规则
        last_id = self._settings.get_last_rule_id()
        if last_id is not None:
            for i in range(self._rule_combo.count()):
                if self._rule_combo.itemData(i) == last_id:
                    self._rule_combo.setCurrentIndex(i)
                    break

        self._rule_mgr_btn = QPushButton("规则管理")
        self._rule_mgr_btn.clicked.connect(self._on_rule_manage)

        rule_layout.addWidget(rule_label)
        rule_layout.addWidget(self._rule_combo, stretch=1)
        rule_layout.addWidget(self._rule_mgr_btn)
        main_layout.addLayout(rule_layout)

        # ---------- 第三部分：文件列表 ----------
        self._file_model = FileTableModel()
        self._sort_proxy = SortProxyModel()
        self._sort_proxy.setSourceModel(self._file_model)

        self._table_view = QTableView()
        self._table_view.setModel(self._sort_proxy)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table_view.setSelectionBehavior(QTableView.SelectRows)
        self._table_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table_view.setEditTriggers(QTableView.NoEditTriggers)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.verticalHeader().setVisible(False)
        self._table_view.setSortingEnabled(True)
        main_layout.addWidget(self._table_view, stretch=1)

        # 表头点击 → 3 态排序
        self._table_view.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        # 右键菜单
        self._table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table_view.customContextMenuRequested.connect(self._on_context_menu)

        # 选择变化 → 更新状态栏
        self._table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed,
        )

        # ---------- 第四部分：操作按钮 ----------
        action_layout = QHBoxLayout()

        self._select_all_btn = QPushButton("选择")
        self._select_all_btn.clicked.connect(self._on_select_all)

        self._deselect_all_btn = QPushButton("取消选择")
        self._deselect_all_btn.clicked.connect(self._on_deselect_all)

        self._rename_btn = QPushButton(self._tr.translate("btn.rename"))
        self._rename_btn.setEnabled(False)
        self._rename_btn.clicked.connect(self._on_rename)

        action_layout.addWidget(self._select_all_btn)
        action_layout.addWidget(self._deselect_all_btn)
        action_layout.addStretch()
        action_layout.addWidget(self._rename_btn)
        main_layout.addLayout(action_layout)

        # ---------- 第五部分：状态栏 ----------
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        self._file_count_label = QLabel("文件：0")
        self._folder_count_label = QLabel("文件夹：0")
        self._selected_count_label = QLabel("已选择：0")
        self._error_count_label = QLabel("错误：0")

        self._status_bar.addWidget(self._file_count_label)
        self._status_bar.addWidget(self._folder_count_label)
        self._status_bar.addWidget(self._selected_count_label)
        self._status_bar.addWidget(self._error_count_label)

    # ---------- 菜单 ----------

    def _setup_menu(self) -> None:
        tr = self._tr
        menu_bar = self.menuBar()
        tools_menu = menu_bar.addMenu(tr.translate("menu.tools"))

        self._undo_action = QAction(tr.translate("menu.undo"), self)
        self._undo_action.setEnabled(False)
        self._undo_action.triggered.connect(self._on_undo)
        tools_menu.addAction(self._undo_action)

        tools_menu.addSeparator()

        log_action = QAction(tr.translate("menu.operation_log"), self)
        log_action.triggered.connect(self._on_show_log)
        tools_menu.addAction(log_action)

        settings_action = QAction(tr.translate("menu.settings"), self)
        settings_action.triggered.connect(self._on_settings)
        tools_menu.addAction(settings_action)

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self._settings, self)
        dialog.exec()

    def _on_show_log(self) -> None:
        dialog = OperationLogDialog(self._logger, self._tr, self)
        dialog.exec()

    def _on_undo(self) -> None:
        if not self._logger.records():
            QMessageBox.information(self, "提示", self._tr.translate("msg.no_undo"))
            return

        results = UndoEngine.undo(self._logger)
        success = sum(1 for r in results if r.success)
        failed = len(results) - success
        QMessageBox.information(
            self, self._tr.translate("msg.undo_done"),
            f"成功：{success}\n失败：{failed}",
        )

        self._undo_action.setEnabled(False)

        if self._current_dir is not None:
            self._start_scan(self._current_dir)

    # ---------- 内部方法 ----------

    def _populate_table(self, items: list[FileItem]) -> None:
        self._file_model.set_items(items)

    def _update_status_bar(self, items: list[FileItem]) -> None:
        file_count = sum(1 for i in items if i.item_type == ItemType.FILE)
        folder_count = sum(1 for i in items if i.item_type == ItemType.DIRECTORY)
        self._file_count_label.setText(f"文件：{file_count}")
        self._folder_count_label.setText(f"文件夹：{folder_count}")
        self._selected_count_label.setText("已选择：0")
        self._error_count_label.setText("错误：0")

    def _current_rule(self) -> Rule | None:
        rule_id = self._rule_combo.currentData()
        if rule_id is None:
            return None
        return self._repo.find(rule_id)

    def _refresh_preview(self) -> None:
        rule = self._current_rule()
        if rule is None or not self._items:
            return
        PreviewEngine.generate_preview(self._items, rule)
        self._file_model.refresh_all()

    def _start_scan(self, directory: Path) -> None:
        if self._scan_worker is not None:
            return

        if _DEBUG:
            t0 = _utime()
            print(f"[UI Profiling] Scan button clicked", flush=True)
            print(f"  Directory: {directory}", flush=True)

        self._browse_btn.setEnabled(False)
        self._refresh_btn.setEnabled(False)
        self._rename_btn.setEnabled(False)

        if _DEBUG:
            t1 = _utime()

        self._scan_worker = ScanWorker([directory], self._current_rule())

        if _DEBUG:
            t2 = _utime()
            print(f"  Prepare/Create:  {(t1-t0)*1000:.1f} ms", flush=True)
            print(f"  Worker created:  {(t2-t1)*1000:.1f} ms", flush=True)

        self._scan_worker.finished.connect(self._on_scan_finished, Qt.QueuedConnection)
        self._scan_worker.start()

        if _DEBUG:
            t3 = _utime()
            print(f"  Thread started:  {(t3-t2)*1000:.1f} ms", flush=True)
            print(f"  TOTAL UI->start: {(t3-t0)*1000:.1f} ms", flush=True)

    def _on_scan_finished(self, _signal_data: list) -> None:
        worker = self._scan_worker
        items: list[FileItem] = worker.items if worker is not None else []

        if _DEBUG:
            t0 = _utime()
            print(f"[UI Profiling] Signal received  t={(t0 - self._scan_t0)*1000:.1f} ms after emit"
                  if hasattr(self, '_scan_t0') else "[UI Profiling] Signal received",
                  flush=True)

        self._items = items
        if _DEBUG:
            t1 = _utime()

        self._populate_table(items)
        if _DEBUG:
            t2 = _utime()

        self._update_status_bar(items)
        if _DEBUG:
            t3 = _utime()

        has_items = len(items) > 0
        self._rename_btn.setEnabled(has_items)
        self._browse_btn.setEnabled(True)
        self._refresh_btn.setEnabled(True)

        # 始终用当前规则重新生成预览（不以 ScanWorker 的为准）
        self._refresh_preview()

        if worker is not None:
            worker.wait()
            worker.deleteLater()
            self._scan_worker = None

        if _DEBUG:
            t4 = _utime()
            print(f"[UI Profiling] _on_scan_finished:", flush=True)
            print(f"  items assign:    {(t1-t0)*1000:.1f} ms", flush=True)
            print(f"  populate_table:  {(t2-t1)*1000:.1f} ms  ({len(items)} rows)", flush=True)
            print(f"  status_bar:      {(t3-t2)*1000:.1f} ms", flush=True)
            print(f"  buttons/cleanup: {(t4-t3)*1000:.1f} ms", flush=True)
            print(f"  TOTAL callback:  {(t4-t0)*1000:.1f} ms", flush=True)
            def _on_paint_done() -> None:
                elapsed = (_utime() - t0) * 1000
                print(f"  UI paint done:   {elapsed:.1f} ms", flush=True)
                print(f"  ═══ TOTAL (signal→paint): {elapsed:.1f} ms ═══", flush=True)
                self._file_model.dump_role_stats()
            QTimer.singleShot(0, _on_paint_done)

    def closeEvent(self, event: object) -> None:
        for w in (self._scan_worker, self._rename_worker):
            if w is not None:
                w.wait(5000)
        self._scan_worker = None
        self._rename_worker = None
        super().closeEvent(event)

    # ---------- 按钮行为 ----------

    def _on_browse(self) -> None:
        chosen = QFileDialog.getExistingDirectory(self, "选择目录")
        if not chosen:
            return
        self._current_dir = Path(chosen)
        self._dir_edit.setText(str(self._current_dir))
        self._start_scan(self._current_dir)

    def _on_refresh(self) -> None:
        if self._current_dir is None:
            QMessageBox.information(self, "提示", "请先选择目录。")
            return
        self._start_scan(self._current_dir)

    def _on_rule_manage(self) -> None:
        dialog = RuleManagerDialog(
            self._repo,
            on_steps_changed=self._refresh_preview,
            parent=self,
        )
        dialog.exec()
        rule_id = self._rule_combo.currentData()
        self._rule_combo.blockSignals(True)
        self._rule_combo.clear()
        for r in self._repo.all_rules():
            self._rule_combo.addItem(r.name, r.id)
        # 恢复之前选中的规则
        if rule_id is not None:
            for i in range(self._rule_combo.count()):
                if self._rule_combo.itemData(i) == rule_id:
                    self._rule_combo.setCurrentIndex(i)
                    break
        self._rule_combo.blockSignals(False)
        self._refresh_preview()

    def _on_rule_changed(self, _index: int) -> None:
        rule_id = self._rule_combo.currentData()
        if isinstance(rule_id, str):
            self._settings.set_last_rule_id(rule_id)
        self._refresh_preview()

    def _on_rename(self) -> None:
        if self._current_dir is None or not self._items:
            QMessageBox.information(self, "提示", "请先选择目录。")
            return

        # 获取所有选中的资源
        sm = self._table_view.selectionModel()
        if sm is None or not sm.selectedRows():
            QMessageBox.information(self, "提示", "请先选择资源。")
            return

        selected_items = [
            self._file_model.item(self._sort_proxy.mapToSource(r).row())
            for r in sm.selectedRows()
        ]

        # 生成 RenamePlan（含完整决策）
        policy = self._settings.get_rename_policy()
        plans = RenamePlanEngine.generate(selected_items, policy)

        # 拦截 INVALID / CONFLICT
        blocked = [p for p in plans if p.status in (
            RenamePlanStatus.INVALID,
            RenamePlanStatus.CONFLICT,
        )]
        if blocked:
            lines = "\n".join(
                f"  {p.source_name} → {p.target_name}: {p.message}"
                for p in blocked[:10]
            )
            if len(blocked) > 10:
                lines += f"\n  ... 共 {len(blocked)} 个错误"
            QMessageBox.warning(self, "校验失败", f"存在 {len(blocked)} 个错误：\n{lines}")
            return

        # 确认
        ready = [p for p in plans if p.action in (RenameAction.RENAME, RenameAction.OVERWRITE)]
        skipped_count = sum(1 for p in plans if p.action == RenameAction.SKIP)
        if not ready:
            msg = "没有需要重命名的资源。"
            if skipped_count:
                msg = f"所有资源均已跳过（{skipped_count} 个）。"
            QMessageBox.information(self, "提示", msg)
            return

        overwrite_count = sum(1 for p in ready if p.action == RenameAction.OVERWRITE)
        msg = f"即将重命名 {len(ready)} 个资源。"
        if overwrite_count:
            msg += f"\n其中 {overwrite_count} 个将覆盖已存在的资源。"
        msg += "\n\n是否继续？"

        reply = QMessageBox.question(
            self, "确认重命名", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        # 后台执行
        self._rename_btn.setEnabled(False)

        progress = QProgressDialog("正在处理...", "", 0, len(plans), self)
        progress.setWindowTitle("正在重命名")
        progress.setCancelButton(None)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()

        self._rename_worker = RenameWorker(plans, logger=self._logger)
        self._rename_worker.progress_changed.connect(progress.setValue, Qt.QueuedConnection)
        self._rename_worker.finished_with_result.connect(
            lambda results: self._on_rename_finished(results, plans, progress),
            Qt.QueuedConnection,
        )
        self._rename_worker.start()

    def _on_rename_finished(
        self, _results: list, plans: list, progress: QProgressDialog,
    ) -> None:
        from models.rename_plan import RenamePlanStatus as S
        progress.close()

        success = sum(1 for p in plans if p.status == S.SUCCESS)
        overwritten = sum(1 for p in plans if p.status == S.OVERWRITTEN)
        skipped = sum(1 for p in plans if p.action == RenameAction.SKIP)
        failed = sum(1 for p in plans if p.status == S.FAILED)

        parts = []
        if success:
            parts.append(f"成功：{success}")
        if overwritten:
            parts.append(f"覆盖：{overwritten}")
        if skipped:
            parts.append(f"跳过：{skipped}")
        if failed:
            parts.append(f"失败：{failed}")

        QMessageBox.information(self, "重命名完成", "\n".join(parts))

        self._rename_btn.setEnabled(True)
        if success + overwritten > 0:
            self._undo_action.setEnabled(True)

        if self._rename_worker is not None:
            self._rename_worker.wait()
            self._rename_worker.deleteLater()
            self._rename_worker = None

        # 重扫目录以获取最新文件状态
        if self._current_dir is not None:
            self._start_scan(self._current_dir)

    def _on_selection_changed(self) -> None:
        sm = self._table_view.selectionModel()
        if sm is not None:
            count = len(sm.selectedRows())
        else:
            count = 0
        self._selected_count_label.setText(f"已选择：{count}")

    def _on_select_all(self) -> None:
        if self._file_model.rowCount() > 0:
            self._table_view.selectAll()

    def _on_deselect_all(self) -> None:
        self._table_view.clearSelection()

    def _on_header_clicked(self, column: int) -> None:
        self._sort_proxy.toggle_sort(column)

    def _on_context_menu(self, pos) -> None:
        index = self._table_view.indexAt(pos)
        if not index.isValid():
            return

        source_idx = self._sort_proxy.mapToSource(index)
        item = self._file_model.item(source_idx.row())
        col = index.column()

        menu = QMenu(self)

        copy_original = menu.addAction("复制原名称")
        copy_original.setEnabled(col in (1, 3))

        copy_new = menu.addAction("复制新名称")
        copy_new.setEnabled(col in (4,) and bool(item.preview_name))

        copy_path = menu.addAction("复制完整路径")
        copy_path.setEnabled(col in (3,))

        action = menu.exec(self._table_view.viewport().mapToGlobal(pos))
        if action == copy_original:
            QApplication.clipboard().setText(item.original_name)
        elif action == copy_new:
            QApplication.clipboard().setText(item.preview_name or "")
        elif action == copy_path:
            QApplication.clipboard().setText(str(item.full_path))
