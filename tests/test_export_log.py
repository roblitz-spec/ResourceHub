from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

from models.operation_record import OperationRecord
from ui.operation_log_dialog import OperationLogDialog


def _make_record(
    ts: str, src: str, tgt: str, success: bool = True, msg: str = "",
) -> OperationRecord:
    return OperationRecord(
        timestamp=datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"),
        source=Path(src), target=Path(tgt),
        success=success, message=msg,
    )


class TestExportLog:
    """导出日志测试（不依赖 QWidget）。"""

    def test_csv_content(self) -> None:
        records = [
            _make_record("2026-01-01 12:00:00", "/a/old.txt", "/a/new.txt"),
        ]
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = Path(f.name)
        try:
            OperationLogDialog._export_csv(records, path)
            content = path.read_text("utf-8")
            assert "time,source,target,result,message" in content
            assert "2026-01-01 12:00:00" in content
            assert '"/a/old.txt"' in content
            assert "成功" in content
        finally:
            path.unlink(missing_ok=True)

    def test_txt_content(self) -> None:
        records = [
            _make_record("2026-01-01 12:00:00", "/a/x.txt", "/a/y.txt",
                         success=False, msg="目标文件已存在"),
        ]
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            path = Path(f.name)
        try:
            OperationLogDialog._export_txt(records, path)
            content = path.read_text("utf-8")
            assert "[2026-01-01 12:00:00]" in content
            assert "/a/x.txt → /a/y.txt" in content
            assert "失败" in content
            assert "目标文件已存在" in content
        finally:
            path.unlink(missing_ok=True)

    def test_empty_records(self) -> None:
        # 静态方法不抛异常，但 UI 层拦截空日志
        path = Path(tempfile.mktemp(suffix=".csv"))
        OperationLogDialog._export_csv([], path)
        content = path.read_text("utf-8")
        assert content == "time,source,target,result,message"
        path.unlink()

    def test_write_error_handled(self) -> None:
        records = [_make_record("2026-01-01 12:00:00", "/a/a.txt", "/a/b.txt")]
        # 写入只读目录
        path = Path("/dev/null/nonexistent/file.csv")
        try:
            OperationLogDialog._export_csv(records, path)
            assert False, "Should have raised"
        except OSError:
            pass  # expected
