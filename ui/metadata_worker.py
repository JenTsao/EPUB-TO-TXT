#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""元信息后台加载：独立 2 线程池，与转换池隔离，防止互相饿死。"""

import threading
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import QObject, Signal

from core.extractors.registry import get_extractor
from core.models import BookMetadata


class MetadataLoader(QObject):
    """request(path) 后台读取元信息，完成后 metadata_ready 信号回主线程。"""

    metadata_ready = Signal(str, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="metadata")
        self._requested: set[str] = set()
        self._lock = threading.Lock()

    def request(self, path: str) -> None:
        with self._lock:
            if path in self._requested:
                return
            self._requested.add(path)
        self._pool.submit(self._load, path)

    def _load(self, path: str) -> None:
        try:
            meta = get_extractor(path).metadata(path)
        except Exception:
            try:
                meta = BookMetadata.from_path(path)
            except Exception:
                return  # 文件在读取前被移动/删除，静默跳过
        self.metadata_ready.emit(path, meta)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False)
