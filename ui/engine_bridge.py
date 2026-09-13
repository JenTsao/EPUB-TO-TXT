#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""引擎回调 → Qt 信号桥：core 线程池 worker 在此把回调转成跨线程安全的信号。"""

from PySide6.QtCore import QObject, Signal


class EngineBridge(QObject):
    """实现 core.engine.ConversionListener 协议；所有信号从 worker 线程 emit，
    Qt 自动使用 QueuedConnection 投递到主线程。"""

    task_started = Signal(str)
    task_progress = Signal(str, float, str)
    task_finished = Signal(str, bool, str, object)
    batch_finished = Signal(int, int)

    def on_task_started(self, path: str) -> None:
        self.task_started.emit(path)

    def on_task_progress(self, path: str, ratio: float, message: str) -> None:
        self.task_progress.emit(path, ratio, message)

    def on_task_finished(self, path: str, ok: bool, message: str, word_count: int | None) -> None:
        self.task_finished.emit(path, ok, message, word_count)

    def on_batch_finished(self, success_count: int, total: int) -> None:
        self.batch_finished.emit(success_count, total)
