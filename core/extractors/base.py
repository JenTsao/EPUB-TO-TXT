#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取器抽象基类、领域异常与任务控制（暂停/取消/进度）。"""

import threading
from abc import ABC, abstractmethod

from core.models import BookMetadata, ExtractionResult


class ConversionError(Exception):
    """转换领域错误基类，UI 层直接展示 message。"""


class UnsupportedFormatError(ConversionError):
    pass


class EncryptedFileError(ConversionError):
    pass


class NoTextLayerError(ConversionError):
    pass


class TaskCancelled(Exception):
    """任务被取消时在检查点抛出。"""


class TaskControl:
    """由引擎下发、worker 只读使用的任务控制柄。

    - checkpoint(): 已取消则抛 TaskCancelled
    - pause_point(): 暂停时阻塞直至恢复，随后再检查取消
    - progress(ratio): 上报单文件内进度（0.0 ~ 1.0）
    """

    def __init__(self, on_progress=None, start_paused: bool = False):
        self._cancel = threading.Event()
        self._resume = threading.Event()
        if not start_paused:
            self._resume.set()
        self._on_progress = on_progress

    def pause(self) -> None:
        self._resume.clear()

    def resume(self) -> None:
        self._resume.set()

    def cancel(self) -> None:
        self._cancel.set()

    def checkpoint(self) -> None:
        if self._cancel.is_set():
            raise TaskCancelled()

    def pause_point(self) -> None:
        self._resume.wait()
        self.checkpoint()

    def progress(self, ratio: float) -> None:
        if self._on_progress is not None:
            self._on_progress(max(0.0, min(1.0, float(ratio))))


class BaseExtractor(ABC):
    """格式提取器接口。

    metadata() 必须轻量（禁止为读取书名而解析全文），供后台元信息线程调用；
    extract() 执行完整提取，应在循环体内调用 control 的检查点与进度上报。
    """

    @abstractmethod
    def metadata(self, path: str) -> BookMetadata:
        """轻量读取元信息，失败时可返回仅含 path/fmt/size 的对象。"""

    @abstractmethod
    def extract(self, path: str, control: TaskControl | None = None) -> ExtractionResult:
        """完整提取文本，返回结构化章节。"""
