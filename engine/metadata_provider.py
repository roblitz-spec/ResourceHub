from __future__ import annotations

from pathlib import Path


class MetadataProvider:
    """惰性元数据提供器 — 仅在首次访问时执行 stat()，结果缓存到实例生命周期。"""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stat: os.stat_result | None = None
        self._stat_error: bool = False

    def _ensure_stat(self) -> None:
        if self._stat is not None or self._stat_error:
            return
        import os
        try:
            self._stat = os.stat(self._path)
        except OSError:
            self._stat_error = True

    @property
    def modified(self) -> float | None:
        self._ensure_stat()
        return self._stat.st_mtime if self._stat else None

    @property
    def created(self) -> float | None:
        self._ensure_stat()
        return self._stat.st_ctime if self._stat else None
