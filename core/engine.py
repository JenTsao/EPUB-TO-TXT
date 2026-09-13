#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""转换引擎：线程池并发调度 + 暂停/取消（纯 stdlib，禁止任何 GUI 依赖）。

UI 通过实现 ConversionListener 协议接收事件；线程安全由 UI 侧的信号桥保证。
"""

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from core.extractors.base import TaskCancelled, TaskControl
from core.extractors.registry import get_extractor
from core.formatters import format_result


class ConversionListener(Protocol):
    def on_task_started(self, path: str) -> None: ...

    def on_task_progress(self, path: str, ratio: float, message: str) -> None: ...

    def on_task_finished(self, path: str, ok: bool, message: str, word_count: int | None) -> None: ...

    def on_batch_finished(self, success_count: int, total: int) -> None: ...


@dataclass
class ConversionOptions:
    output_dir: str
    output_format: str  # txt / md / html / epub


def unique_output_path(output_dir: str, filename: str) -> Path:
    """处理重名冲突：已存在时追加 (2)、(3)… 序号，避免不同目录同名文件互相覆盖。"""
    target = Path(output_dir) / filename
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    for counter in range(2, 10000):
        candidate = target.with_name(f"{stem} ({counter}){suffix}")
        if not candidate.exists():
            return candidate
    return target


class ConversionEngine:
    def __init__(self, listener: ConversionListener, max_workers: int | None = None):
        self._listener = listener
        self._max_workers = max_workers or min(4, os.cpu_count() or 2)
        self._pool = ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="convert")
        self._lock = threading.Lock()
        self._controls: list[TaskControl] = []
        self._running = False
        self._paused = False
        self._batch_done = threading.Event()

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def wait(self, timeout: float | None = None) -> bool:
        """阻塞等待当前批次完成（供 CLI / 测试使用），返回是否在超时前完成。"""
        return self._batch_done.wait(timeout)

    def submit(self, files: list[str], options: ConversionOptions) -> None:
        Path(options.output_dir).mkdir(parents=True, exist_ok=True)
        self._batch_done.clear()
        with self._lock:
            if self._running:
                raise RuntimeError("已有转换任务在进行中")
            self._running = True
            self._paused = False
            self._controls = []

        total = len(files)
        counters = {"finished": 0, "success": 0}

        def finalize(ok: bool) -> None:
            done = False
            with self._lock:
                counters["finished"] += 1
                if ok:
                    counters["success"] += 1
                done = counters["finished"] >= total
            if done:
                with self._lock:
                    self._running = False
                self._batch_done.set()
                self._listener.on_batch_finished(counters["success"], total)

        for path in files:
            progress_cb = lambda ratio, p=path: self._listener.on_task_progress(p, ratio, "")
            control = TaskControl(on_progress=progress_cb, start_paused=False)
            with self._lock:
                self._controls.append(control)
            self._pool.submit(self._run_task, path, options, control, finalize)

    def _run_task(self, path: str, options: ConversionOptions, control: TaskControl, finalize) -> None:
        name = Path(path).name
        ok = False
        try:
            control.checkpoint()
            self._listener.on_task_started(path)
            extractor = get_extractor(path)
            result = extractor.extract(path, control)
            content, filename = format_result(result, options.output_format, path)
            output_path = unique_output_path(options.output_dir, filename)
            if isinstance(content, bytes):
                output_path.write_bytes(content)
            else:
                output_path.write_text(content, encoding="utf-8")
            ok = True
            self._listener.on_task_finished(
                path, True, f"成功转换：{output_path.name}", result.word_count
            )
        except TaskCancelled:
            self._listener.on_task_finished(path, False, "已取消", None)
        except Exception as e:
            self._listener.on_task_finished(path, False, f"转换失败 {name}：{e}", None)
        finally:
            finalize(ok)

    def pause(self) -> None:
        with self._lock:
            self._paused = True
            controls = list(self._controls)
        for control in controls:
            control.pause()

    def resume(self) -> None:
        with self._lock:
            self._paused = False
            controls = list(self._controls)
        for control in controls:
            control.resume()

    def cancel(self) -> None:
        with self._lock:
            self._paused = False
            controls = list(self._controls)
        for control in controls:
            # 先恢复再取消，确保阻塞在暂停点的线程能醒来并观察到取消
            control.resume()
            control.cancel()

    def shutdown(self, wait: bool = False) -> None:
        self.cancel()
        self._pool.shutdown(wait=wait)
