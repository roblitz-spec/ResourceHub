"""Regex Assistant — 非模态参考窗口，内置模板和帮助。"""
from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.regex_templates import TEMPLATES

_SETTINGS_GROUP = "RegexAssistant"
_HELP_TEXT = """\
<table>
<tr><td><b>语法</b></td><td><b>含义</b></td></tr>
<tr><td><code>.</code></td><td>任意字符</td></tr>
<tr><td><code>.*</code></td><td>任意数量字符</td></tr>
<tr><td><code>\\d</code></td><td>数字 [0-9]</td></tr>
<tr><td><code>\\w</code></td><td>单词字符 [a-zA-Z0-9_]</td></tr>
<tr><td><code>\\s</code></td><td>空白字符</td></tr>
<tr><td><code>^</code></td><td>字符串开头</td></tr>
<tr><td><code>$</code></td><td>字符串结尾</td></tr>
<tr><td><code>(...)</code></td><td>捕获组</td></tr>
<tr><td><code>\\1</code></td><td>第一个捕获组</td></tr>
<tr><td><code>\\2</code></td><td>第二个捕获组</td></tr>
<tr><td><code>[abc]</code></td><td>字符类（a/b/c 之一）</td></tr>
<tr><td><code>[^abc]</code></td><td>否定字符类</td></tr>
<tr><td><code>+</code></td><td>1 个或更多</td></tr>
<tr><td><code>*</code></td><td>0 个或更多</td></tr>
<tr><td><code>?</code></td><td>0 个或 1 个（非贪婪: *? / +?）</td></tr>
</table>

<h4>示例</h4>

<p><b>例 1：移除方括号标签</b></p>
<table>
<tr><td>Before</td><td><code>【你好】ABC123</code></td></tr>
<tr><td>Regex</td><td><code>【.*?】</code></td></tr>
<tr><td>After</td><td><code>ABC123</code></td></tr>
</table>

<p><b>例 2：移除分辨率后缀</b></p>
<table>
<tr><td>Before</td><td><code>ABC(1080P)</code></td></tr>
<tr><td>Regex</td><td><code>\\(.*?\\)</code></td></tr>
<tr><td>After</td><td><code>ABC</code></td></tr>
</table>

<p><b>例 3：提取编号</b></p>
<table>
<tr><td>Before</td><td><code>IMG_0001</code></td></tr>
<tr><td>Regex</td><td><code>IMG_</code></td></tr>
<tr><td>Replacement</td><td><i>(空)</i></td></tr>
<tr><td>After</td><td><code>0001</code></td></tr>
</table>
"""


class RegexAssistant(QDialog):
    """Regex 参考助手 — 非模态，可保持打开。"""

    def __init__(self, on_insert=None, parent=None):
        super().__init__(parent)
        self._on_insert = on_insert
        self._settings = QSettings("ResourceHub", "ResourceHub")

        self.setWindowTitle("Regex Assistant")
        self.setMinimumSize(520, 440)
        self._restore_geometry()

        root = QVBoxLayout(self)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_templates_tab(), "Templates")
        self._tabs.addTab(self._build_help_tab(), "Help")
        root.addWidget(self._tabs)

        self._restore_tab()

    # ── Templates Tab ────────────────────────────────────

    def _build_templates_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)

        splitter = QSplitter(Qt.Horizontal)

        # 左边：分类模板列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self._template_list = QListWidget()

        categories: dict[str, list[dict]] = {}
        for t in TEMPLATES:
            categories.setdefault(t["category"], []).append(t)

        for cat in sorted(categories):
            header = QListWidgetItem(f"── {cat} ──")
            header.setFlags(Qt.NoItemFlags)
            self._template_list.addItem(header)
            for t in categories[cat]:
                item = QListWidgetItem(t["name"])
                item.setData(1, t)
                self._template_list.addItem(item)

        self._template_list.currentItemChanged.connect(self._on_template_selected)
        left_layout.addWidget(self._template_list)
        splitter.addWidget(left)

        # 右边：模板详情 + 插入按钮
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        detail = QGroupBox("模板详情")
        detail_layout = QVBoxLayout(detail)

        self._t_name = QLabel()
        self._t_name.setStyleSheet("font-weight: bold; font-size: 13px;")
        self._t_desc = QLabel()
        self._t_desc.setWordWrap(True)

        self._t_pattern = QLabel()
        self._t_pattern.setStyleSheet("font-family: monospace;")
        self._t_replacement = QLabel()
        self._t_replacement.setStyleSheet("font-family: monospace;")

        example_group = QGroupBox("示例")
        example_layout = QVBoxLayout(example_group)
        self._t_before = QLabel()
        self._t_after = QLabel()

        example_layout.addWidget(self._t_before)
        example_layout.addWidget(QLabel("↓"))
        example_layout.addWidget(self._t_after)

        detail_layout.addWidget(self._t_name)
        detail_layout.addWidget(self._t_desc)
        detail_layout.addWidget(QLabel("Regex:"))
        detail_layout.addWidget(self._t_pattern)
        detail_layout.addWidget(QLabel("Replacement:"))
        detail_layout.addWidget(self._t_replacement)
        detail_layout.addWidget(example_group)

        right_layout.addWidget(detail)

        self._insert_btn = QPushButton("Insert Template")
        self._insert_btn.setEnabled(False)
        self._insert_btn.clicked.connect(self._on_insert_clicked)
        right_layout.addWidget(self._insert_btn)

        splitter.addWidget(right)
        splitter.setSizes([200, 300])
        layout.addWidget(splitter)

        return page

    def _on_template_selected(self, current, _prev):
        if current is None or not current.flags():
            self._insert_btn.setEnabled(False)
            return
        t = current.data(1)
        if t is None:
            self._insert_btn.setEnabled(False)
            return

        self._current_template = t
        self._t_name.setText(t["name"])
        self._t_desc.setText(t["description"])
        self._t_pattern.setText(t["pattern"])
        self._t_replacement.setText(t["replacement"] or "(空)")
        self._t_before.setText(t["example_before"])
        self._t_after.setText(t["example_after"])
        self._insert_btn.setEnabled(True)

    def _on_insert_clicked(self):
        if self._on_insert is not None:
            self._on_insert(
                self._current_template["pattern"],
                self._current_template["replacement"],
            )

    @staticmethod
    def confirm_overwrite(parent) -> bool:
        return (
            QMessageBox.question(
                parent,
                "确认覆盖",
                "当前 Regex 和 Replacement 将被替换。\n\n是否继续？",
                QMessageBox.Ok | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )
            == QMessageBox.Ok
        )

    # ── Help Tab ─────────────────────────────────────────

    def _build_help_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml(_HELP_TEXT)
        layout.addWidget(help_text)
        return page

    # ── Geometry Persistence ────────────────────────────

    def _restore_geometry(self):
        geo = self._settings.value(f"{_SETTINGS_GROUP}/geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self.resize(520, 440)

    def _save_geometry(self):
        self._settings.setValue(f"{_SETTINGS_GROUP}/geometry", self.saveGeometry())

    def _restore_tab(self):
        idx = self._settings.value(f"{_SETTINGS_GROUP}/tab", 0)
        if isinstance(idx, int) and 0 <= idx < self._tabs.count():
            self._tabs.setCurrentIndex(idx)

    def _save_tab(self):
        self._settings.setValue(f"{_SETTINGS_GROUP}/tab", self._tabs.currentIndex())

    def closeEvent(self, event):
        self._save_geometry()
        self._save_tab()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
