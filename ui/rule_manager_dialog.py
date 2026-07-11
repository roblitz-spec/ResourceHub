from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt as QtCore
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from models.rule import Rule
from models.rule_step import RuleStep
from storage.repository import RuleRepository

_STEP_TYPES: list[tuple[str, str, str, str]] = [
    # (type, label, category, icon)
    ("replace",       "文本替换",   "文本处理", "🔤"),
    ("remove_text",   "删除文本",   "文本处理", "✂️"),
    ("regex_replace", "正则替换",   "文本处理", "⭐"),
    ("trim",          "去除空白",   "文本处理", "🧹"),
    ("case",          "大小写转换", "文本处理", "🔠"),
    ("number",        "编号",       "文本处理", "🔢"),
    ("insert",        "插入文本",   "文本处理", "📝"),
    ("date",          "日期",       "文本处理", "📅"),
    ("add_prefix",    "添加前缀",   "添加",    "➕"),
]

_STEP_DEFAULTS: dict[str, dict[str, object]] = {
    "replace":       {"from": "", "to": ""},
    "remove_text":   {"text": ""},
    "add_prefix":    {"text": ""},
    "regex_replace": {"pattern": "", "replacement": ""},
    "case":          {"mode": "upper"},
    "trim":          {"mode": "both"},
    "number":        {"start": "1", "step": "1", "padding": "3", "position": "prefix"},
    "insert":        {"text": "", "at_index": "0"},
    "date":          {"source": "modified", "format": "%Y-%m-%d", "position": "prefix", "separator": "_"},
}


class RuleManagerDialog(QDialog):
    """规则管理对话框 —— 新增 / 编辑 / 删除规则 + RuleStep 编辑。"""

    def __init__(
        self,
        repo: RuleRepository,
        on_steps_changed: Callable[[], None] | None = None,
        parent: QDialog | None = None,
    ) -> None:
        super().__init__(parent)
        self._repo = repo
        self._current_rule: Rule | None = None
        self._on_steps_changed = on_steps_changed

        self.setWindowTitle("规则管理")
        self.resize(900, 550)

        root = QHBoxLayout(self)

        # ── 左侧：规则列表 ──
        left = QVBoxLayout()
        left.addWidget(QLabel("规则列表"))
        self._rule_list = QListWidget()
        self._rule_list.currentItemChanged.connect(self._on_rule_selected)
        left.addWidget(self._rule_list, stretch=1)
        root.addLayout(left, stretch=1)

        # ── 右侧 ──
        right = QVBoxLayout()

        # 规则名称
        right.addWidget(QLabel("规则名称"))
        self._name_edit = QLineEdit()
        right.addWidget(self._name_edit)

        # 规则说明
        right.addWidget(QLabel("规则说明"))
        self._desc_edit = QPlainTextEdit()
        self._desc_edit.setMaximumHeight(60)
        right.addWidget(self._desc_edit)

        # ── 步骤区域 ──
        step_group = QGroupBox("步骤")
        step_layout = QVBoxLayout(step_group)

        step_toolbar = QHBoxLayout()
        self._add_step_btn = QPushButton("新增步骤")
        self._add_step_btn.clicked.connect(self._on_add_step)
        self._del_step_btn = QPushButton("删除步骤")
        self._del_step_btn.clicked.connect(self._on_delete_step)
        self._up_btn = QPushButton("↑")
        self._up_btn.clicked.connect(self._on_move_up)
        self._down_btn = QPushButton("↓")
        self._down_btn.clicked.connect(self._on_move_down)

        step_toolbar.addWidget(self._add_step_btn)
        step_toolbar.addWidget(self._del_step_btn)
        step_toolbar.addStretch()
        step_toolbar.addWidget(self._up_btn)
        step_toolbar.addWidget(self._down_btn)
        step_layout.addLayout(step_toolbar)

        self._step_list = QListWidget()
        self._step_list.currentItemChanged.connect(self._on_step_selected)
        step_layout.addWidget(self._step_list)

        right.addWidget(step_group, stretch=1)

        # ── 步骤参数编辑（QStackedWidget，7 页）──
        self._param_stack = QStackedWidget()

        def _make_page() -> tuple[QWidget, QFormLayout]:
            w = QWidget()
            return w, QFormLayout(w)

        # 0: 空页
        self._param_stack.addWidget(QLabel("选择一个步骤以编辑参数"))

        # 1: replace
        pg, _ = _make_page(); self._replace_from = QLineEdit(); self._replace_to = QLineEdit()
        self._replace_from.setPlaceholderText("要查找的文字")
        self._replace_to.setPlaceholderText("替换为")
        _.addRow("查找：", self._replace_from); _.addRow("替换为：", self._replace_to)
        self._param_stack.addWidget(pg)

        # 2: remove_text
        pg, _ = _make_page(); self._remove_text_edit = QLineEdit()
        self._remove_text_edit.setPlaceholderText("要删除的文字")
        _.addRow("删除：", self._remove_text_edit)
        self._param_stack.addWidget(pg)

        # 3: add_prefix
        pg, _ = _make_page(); self._prefix_edit = QLineEdit()
        self._prefix_edit.setPlaceholderText("要添加的前缀")
        _.addRow("前缀：", self._prefix_edit)
        self._param_stack.addWidget(pg)

        # 4: regex_replace
        pg, _ = _make_page(); self._regex_pat = QLineEdit(); self._regex_repl = QLineEdit(); self._regex_flags = QLineEdit()
        self._regex_pat.setPlaceholderText("例如 \\d+p$")
        self._regex_repl.setPlaceholderText("支持 \\1 分组引用")
        self._regex_flags.setPlaceholderText("可选：I=忽略大小写 M=多行")
        _.addRow("匹配表达式：", self._regex_pat); _.addRow("替换内容：", self._regex_repl); _.addRow("标志位：", self._regex_flags)
        self._param_stack.addWidget(pg)

        # 5: case
        pg, _ = _make_page(); self._case_mode = QComboBox()
        self._case_mode.addItems(["全部大写", "全部小写", "首字母大写", "词首大写"])
        self._case_mode.setItemData(0, "upper")
        self._case_mode.setItemData(1, "lower")
        self._case_mode.setItemData(2, "capitalize")
        self._case_mode.setItemData(3, "title")
        _.addRow("模式：", self._case_mode)
        self._param_stack.addWidget(pg)

        # 6: trim
        pg, _ = _make_page(); self._trim_mode = QComboBox()
        self._trim_mode.addItems(["两侧", "左侧", "右侧"])
        self._trim_mode.setItemData(0, "both")
        self._trim_mode.setItemData(1, "left")
        self._trim_mode.setItemData(2, "right")
        _.addRow("模式：", self._trim_mode)
        self._param_stack.addWidget(pg)

        # 7: number
        pg, _ = _make_page()
        self._num_start = QSpinBox(); self._num_start.setRange(0, 999999); self._num_start.setValue(1)
        self._num_step = QSpinBox(); self._num_step.setRange(1, 9999); self._num_step.setValue(1)
        self._num_pad = QSpinBox(); self._num_pad.setRange(0, 10); self._num_pad.setValue(3); self._num_pad.setSpecialValueText("不补零")
        self._num_pos = QComboBox(); self._num_pos.addItems(["前缀", "后缀"])
        self._num_pos.setItemData(0, "prefix"); self._num_pos.setItemData(1, "suffix")
        _.addRow("起始编号：", self._num_start); _.addRow("步长：", self._num_step)
        _.addRow("位数：", self._num_pad); _.addRow("位置：", self._num_pos)
        self._param_stack.addWidget(pg)

        # 8: insert
        pg, _ = _make_page()
        self._ins_text = QLineEdit(); self._ins_text.setPlaceholderText("要插入的文字")
        self._ins_idx = QSpinBox(); self._ins_idx.setRange(-1, 999); self._ins_idx.setValue(0); self._ins_idx.setSpecialValueText("开头")
        _.addRow("插入文字：", self._ins_text)
        _.addRow("插入位置：", self._ins_idx)
        self._param_stack.addWidget(pg)

        # 9: date
        pg, _ = _make_page()
        self._date_src = QComboBox(); self._date_src.addItems(["修改时间"]); self._date_src.setItemData(0, "modified")
        self._date_fmt = QLineEdit(); self._date_fmt.setText("%Y-%m-%d"); self._date_fmt.setPlaceholderText("例如 %Y-%m-%d")
        self._date_sep = QLineEdit(); self._date_sep.setText("_"); self._date_sep.setPlaceholderText("分隔符，可留空")
        self._date_pos = QComboBox(); self._date_pos.addItems(["前缀", "后缀"])
        self._date_pos.setItemData(0, "prefix"); self._date_pos.setItemData(1, "suffix")
        _.addRow("时间来源：", self._date_src); _.addRow("格式：", self._date_fmt)
        _.addRow("分隔符：", self._date_sep); _.addRow("位置：", self._date_pos)
        self._param_stack.addWidget(pg)

        right.addWidget(self._param_stack)

        # 信号连接
        for edit in (self._replace_from, self._replace_to, self._remove_text_edit,
                     self._prefix_edit, self._regex_pat, self._regex_repl, self._regex_flags):
            edit.textChanged.connect(self._on_param_changed)
        self._case_mode.currentIndexChanged.connect(lambda: self._on_param_changed())
        self._trim_mode.currentIndexChanged.connect(lambda: self._on_param_changed())
        self._num_start.valueChanged.connect(lambda: self._on_param_changed())
        self._num_step.valueChanged.connect(lambda: self._on_param_changed())
        self._num_pad.valueChanged.connect(lambda: self._on_param_changed())
        self._num_pos.currentIndexChanged.connect(lambda: self._on_param_changed())
        self._ins_text.textChanged.connect(self._on_param_changed)
        self._ins_idx.valueChanged.connect(lambda: self._on_param_changed())
        self._date_fmt.textChanged.connect(self._on_param_changed)
        self._date_sep.textChanged.connect(self._on_param_changed)
        self._date_src.currentIndexChanged.connect(lambda: self._on_param_changed())
        self._date_pos.currentIndexChanged.connect(lambda: self._on_param_changed())

        # ── 底部按钮 ──
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("新增", clicked=self._on_add_rule))
        btn_layout.addWidget(QPushButton("删除", clicked=self._on_delete_rule))
        btn_layout.addStretch()
        btn_layout.addWidget(QPushButton("保存", clicked=self._on_save))
        btn_layout.addWidget(QPushButton("关闭", clicked=self.close))
        right.addLayout(btn_layout)

        root.addLayout(right, stretch=2)

        self._refresh_rule_list()

    # ============================================================
    #  规则列表
    # ============================================================

    def _refresh_rule_list(self) -> None:
        self._rule_list.clear()
        for rule in self._repo.all_rules():
            item = QListWidgetItem(rule.name)
            item.setData(1, rule.id)
            self._rule_list.addItem(item)

    def _select_rule_in_list(self, rule_id: str) -> None:
        for i in range(self._rule_list.count()):
            if self._rule_list.item(i).data(1) == rule_id:
                self._rule_list.setCurrentRow(i)
                return

    def _generate_id(self) -> str:
        existing = {r.id for r in self._repo.all_rules()}
        idx = 1
        while f"rule_{idx}" in existing:
            idx += 1
        return f"rule_{idx}"

    def _on_rule_selected(
        self, current: QListWidgetItem | None, _prev: QListWidgetItem | None,
    ) -> None:
        if current is None:
            self._current_rule = None
            self._name_edit.clear()
            self._desc_edit.clear()
            self._refresh_step_list()
            return
        rule_id = current.data(1)
        self._current_rule = self._repo.find(rule_id)
        if self._current_rule:
            self._name_edit.setText(self._current_rule.name)
            self._desc_edit.setPlainText(self._current_rule.description)
            self._refresh_step_list()

    def _on_add_rule(self) -> None:
        new_rule = Rule(id=self._generate_id(), name="新规则", steps=[])
        self._repo.add(new_rule)
        self._repo.save()
        self._refresh_rule_list()
        self._select_rule_in_list(new_rule.id)

    def _on_delete_rule(self) -> None:
        if self._current_rule is None:
            return
        if self._current_rule.id == "default":
            QMessageBox.warning(self, "提示", "默认规则不可删除。")
            return
        self._repo.remove(self._current_rule.id)
        self._repo.save()
        self._current_rule = None
        self._name_edit.clear()
        self._desc_edit.clear()
        self._refresh_rule_list()
        self._refresh_step_list()

    # ============================================================
    #  Step 列表
    # ============================================================

    def _refresh_step_list(self) -> None:
        self._step_list.clear()
        self._param_stack.setCurrentIndex(0)
        if self._current_rule is None:
            return
        for step in self._current_rule.steps:
            p = step.parameters
            label = {
                "replace": f"替换  {p.get('from', '?')} → {p.get('to', '?')}",
                "remove_text": f"删除  \"{p.get('text', '?')}\"",
                "add_prefix": f"前缀  \"{p.get('text', '?')}\"",
                "regex_replace": f"正则  /{p.get('pattern', '?')}/ → \"{p.get('replacement', '')}\"",
                "case": f"大小写  {p.get('mode', '?')}",
                "trim": f"去空白  {p.get('mode', 'both')}",
                "number": f"编号  #{p.get('start','1')}+{p.get('step','1')} pad={p.get('padding','3')}",
                "insert": f"插入  \"{p.get('text','?')}\" @{p.get('at_index','0')}",
                "date": f"日期  {p.get('format','?')} ({p.get('position','?')})",
            }.get(step.type, step.type)
            item = QListWidgetItem(label)
            item.setData(1, id(step))
            self._step_list.addItem(item)

    def _current_step(self) -> RuleStep | None:
        if self._current_rule is None:
            return None
        item = self._step_list.currentItem()
        if item is None:
            return None
        step_id = item.data(1)
        for s in self._current_rule.steps:
            if id(s) == step_id:
                return s
        return None

    _PAGE_INDEX: dict[str, int] = {
        "replace": 1, "remove_text": 2, "add_prefix": 3,
        "regex_replace": 4, "case": 5, "trim": 6, "number": 7, "insert": 8, "date": 9,
    }

    def _on_step_selected(
        self, current: QListWidgetItem | None, _prev: QListWidgetItem | None,
    ) -> None:
        step = self._current_step()
        if step is None:
            self._param_stack.setCurrentIndex(0)
            return
        tp = step.type
        params = step.parameters
        page = self._PAGE_INDEX.get(tp, 0)

        if page == 1:  # replace
            self._replace_from.blockSignals(True)
            self._replace_to.blockSignals(True)
            self._replace_from.setText(str(params.get("from", "")))
            self._replace_to.setText(str(params.get("to", "")))
            self._replace_from.blockSignals(False)
            self._replace_to.blockSignals(False)
        elif page == 2:  # remove_text
            self._remove_text_edit.blockSignals(True)
            self._remove_text_edit.setText(str(params.get("text", "")))
            self._remove_text_edit.blockSignals(False)
        elif page == 3:  # add_prefix
            self._prefix_edit.blockSignals(True)
            self._prefix_edit.setText(str(params.get("text", "")))
            self._prefix_edit.blockSignals(False)
        elif page == 4:  # regex_replace
            self._regex_pat.blockSignals(True); self._regex_repl.blockSignals(True); self._regex_flags.blockSignals(True)
            self._regex_pat.setText(str(params.get("pattern", "")))
            self._regex_repl.setText(str(params.get("replacement", "")))
            self._regex_flags.setText(str(params.get("flags", "")))
            self._regex_pat.blockSignals(False); self._regex_repl.blockSignals(False); self._regex_flags.blockSignals(False)
        elif page == 5:  # case
            self._case_mode.blockSignals(True)
            target = str(params.get("mode", "upper"))
            for i in range(self._case_mode.count()):
                if self._case_mode.itemData(i) == target:
                    self._case_mode.setCurrentIndex(i)
                    break
            self._case_mode.blockSignals(False)
        elif page == 6:  # trim
            self._trim_mode.blockSignals(True)
            target = str(params.get("mode", "both"))
            for i in range(self._trim_mode.count()):
                if self._trim_mode.itemData(i) == target:
                    self._trim_mode.setCurrentIndex(i)
                    break
            self._trim_mode.blockSignals(False)
        elif page == 7:  # number
            self._num_start.blockSignals(True); self._num_step.blockSignals(True)
            self._num_pad.blockSignals(True); self._num_pos.blockSignals(True)
            self._num_start.setValue(int(str(params.get("start", "1"))))
            self._num_step.setValue(int(str(params.get("step", "1"))))
            self._num_pad.setValue(int(str(params.get("padding", "3"))))
            target = str(params.get("position", "prefix"))
            for i in range(self._num_pos.count()):
                if self._num_pos.itemData(i) == target:
                    self._num_pos.setCurrentIndex(i); break
            self._num_start.blockSignals(False); self._num_step.blockSignals(False)
            self._num_pad.blockSignals(False); self._num_pos.blockSignals(False)
        elif page == 8:  # insert
            self._ins_text.blockSignals(True); self._ins_idx.blockSignals(True)
            self._ins_text.setText(str(params.get("text", "")))
            self._ins_idx.setValue(int(str(params.get("at_index", "0"))))
            self._ins_text.blockSignals(False); self._ins_idx.blockSignals(False)
        elif page == 9:  # date
            self._date_src.blockSignals(True); self._date_fmt.blockSignals(True)
            self._date_sep.blockSignals(True); self._date_pos.blockSignals(True)
            target_src = str(params.get("source", "modified"))
            for i in range(self._date_src.count()):
                if self._date_src.itemData(i) == target_src:
                    self._date_src.setCurrentIndex(i); break
            self._date_fmt.setText(str(params.get("format", "%Y-%m-%d")))
            self._date_sep.setText(str(params.get("separator", "_")))
            target_pos = str(params.get("position", "prefix"))
            for i in range(self._date_pos.count()):
                if self._date_pos.itemData(i) == target_pos:
                    self._date_pos.setCurrentIndex(i); break
            self._date_src.blockSignals(False); self._date_fmt.blockSignals(False)
            self._date_sep.blockSignals(False); self._date_pos.blockSignals(False)

        self._param_stack.setCurrentIndex(page)

    def _notify_steps_changed(self) -> None:
        if self._on_steps_changed is not None:
            self._on_steps_changed()

    # ============================================================
    #  Step 操作
    # ============================================================

    def _on_add_step(self) -> None:
        if self._current_rule is None:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("选择步骤类型")
        layout = QVBoxLayout(dlg)
        lst = QListWidget()
        cats: dict[str, list[tuple[str, str, str]]] = {}
        for tp, label, cat, icon in _STEP_TYPES:
            cats.setdefault(cat, []).append((tp, label, icon))
        for cat in sorted(cats):
            header = QListWidgetItem(f"── {cat} ──")
            header.setFlags(QtCore.NoItemFlags)
            lst.addItem(header)
            for tp, label, icon in cats[cat]:
                item = QListWidgetItem(f"{icon}  {label}")
                item.setData(1, tp)
                lst.addItem(item)
        layout.addWidget(lst)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(dlg.accept)
        btn.rejected.connect(dlg.reject)
        layout.addWidget(btn)
        if dlg.exec() != QDialog.Accepted:
            return
        cur = lst.currentItem()
        if cur is None or not cur.flags():
            return
        tp = cur.data(1)
        params = dict(_STEP_DEFAULTS.get(tp, {}))
        step = RuleStep(type=tp, parameters=params)
        self._current_rule.steps.append(step)
        self._refresh_step_list()
        self._step_list.setCurrentRow(self._step_list.count() - 1)
        self._notify_steps_changed()

    def _on_delete_step(self) -> None:
        step = self._current_step()
        if step is None:
            return
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除该步骤吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._current_rule.steps.remove(step)
        self._refresh_step_list()
        self._notify_steps_changed()

    def _on_move_up(self) -> None:
        if self._current_rule is None:
            return
        idx = self._step_list.currentRow()
        if idx <= 0:
            return
        steps = self._current_rule.steps
        steps[idx], steps[idx - 1] = steps[idx - 1], steps[idx]
        self._refresh_step_list()
        self._step_list.setCurrentRow(idx - 1)
        self._notify_steps_changed()

    def _on_move_down(self) -> None:
        if self._current_rule is None:
            return
        idx = self._step_list.currentRow()
        if idx < 0 or idx >= len(self._current_rule.steps) - 1:
            return
        steps = self._current_rule.steps
        steps[idx], steps[idx + 1] = steps[idx + 1], steps[idx]
        self._refresh_step_list()
        self._step_list.setCurrentRow(idx + 1)
        self._notify_steps_changed()

    def _on_param_changed(self) -> None:
        step = self._current_step()
        if step is None:
            return
        tp = step.type
        if tp == "replace":
            step.parameters["from"] = self._replace_from.text()
            step.parameters["to"] = self._replace_to.text()
        elif tp == "remove_text":
            step.parameters["text"] = self._remove_text_edit.text()
        elif tp == "add_prefix":
            step.parameters["text"] = self._prefix_edit.text()
        elif tp == "regex_replace":
            step.parameters["pattern"] = self._regex_pat.text()
            step.parameters["replacement"] = self._regex_repl.text()
            step.parameters["flags"] = self._regex_flags.text()
        elif tp == "case":
            step.parameters["mode"] = self._case_mode.currentData()
        elif tp == "trim":
            step.parameters["mode"] = self._trim_mode.currentData()
        elif tp == "number":
            step.parameters["start"] = str(self._num_start.value())
            step.parameters["step"] = str(self._num_step.value())
            step.parameters["padding"] = str(self._num_pad.value())
            step.parameters["position"] = self._num_pos.currentData()
        elif tp == "insert":
            step.parameters["text"] = self._ins_text.text()
            step.parameters["at_index"] = str(self._ins_idx.value())
        elif tp == "date":
            step.parameters["source"] = self._date_src.currentData()
            step.parameters["format"] = self._date_fmt.text()
            step.parameters["separator"] = self._date_sep.text()
            step.parameters["position"] = self._date_pos.currentData()
        self._notify_steps_changed()
        row = self._step_list.currentRow()
        self._refresh_step_list()
        self._step_list.setCurrentRow(row)

    # ============================================================
    #  保存 & 校验
    # ============================================================

    def _validate(self) -> list[str]:
        errors: list[str] = []
        if self._current_rule is None:
            return errors

        name = self._name_edit.text().strip()
        if not name:
            errors.append("规则名称不能为空。")

        for r in self._repo.all_rules():
            if r.id != self._current_rule.id and r.name == name:
                errors.append(f"规则名称「{name}」已存在。")
                break

        for step in self._current_rule.steps:
            if step.type == "replace" and not str(step.parameters.get("from", "")):
                errors.append("Replace 步骤的 from 不能为空。")
            if step.type == "regex_replace" and not str(step.parameters.get("pattern", "")):
                errors.append("Regex Replace 步骤的 pattern 不能为空。")

        return errors

    def _on_save(self) -> None:
        if self._current_rule is None:
            return

        errors = self._validate()
        if errors:
            QMessageBox.warning(self, "校验失败", "\n".join(errors))
            return

        for step in self._current_rule.steps:
            if step.type == "add_prefix" and not str(step.parameters.get("text", "")):
                QMessageBox.information(
                    self, "提示",
                    "Add Prefix 步骤的 prefix 为空，这不会改变文件名。",
                )
                break

        self._current_rule.name = self._name_edit.text().strip() or self._current_rule.name
        self._current_rule.description = self._desc_edit.toPlainText()
        self._repo.save()

        rule_id = self._current_rule.id  # 在 refresh 之前保存 id
        self._rule_list.blockSignals(True)
        self._refresh_rule_list()
        self._select_rule_in_list(rule_id)
        self._rule_list.blockSignals(False)
        self._notify_steps_changed()
