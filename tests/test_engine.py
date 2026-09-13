"""转换引擎测试：事件序列、暂停/取消、并发与重名处理。"""

import threading
import time
from dataclasses import dataclass, field

import pytest

from core.engine import ConversionEngine, ConversionOptions, unique_output_path
from core.extractors.base import TaskControl
from core.models import BookMetadata, Chapter, ExtractionResult


@dataclass
class FakeListener:
    events: list = field(default_factory=list)
    batch_event: threading.Event = field(default_factory=threading.Event)
    started: threading.Event = field(default_factory=threading.Event)

    def on_task_started(self, path):
        self.events.append(("started", path))
        self.started.set()

    def on_task_progress(self, path, ratio, message):
        self.events.append(("progress", path, ratio))

    def on_task_finished(self, path, ok, message, word_count):
        self.events.append(("finished", path, ok, message, word_count))

    def on_batch_finished(self, success_count, total):
        self.events.append(("batch", success_count, total))
        self.batch_event.set()


def _make_extractor(delay=0.0, mode="plain", gate=None):
    """构造可控的假提取器。

    mode="gate":  先阻塞在 gate 上（由测试控制放行时机），随后 checkpoint——
                  用于取消测试（cancel 后放行，worker 在 checkpoint 抛出）。
    mode="pause": gate 放行后调用 pause_point——用于暂停测试（pause 期间阻塞）。
    """

    class SlowExtractor:
        def metadata(self, path):
            return BookMetadata.from_path(path)

        def extract(self, path, control=None):
            control = control or TaskControl()
            control.checkpoint()
            if mode in ("gate", "pause") and gate is not None:
                gate.wait(10)
            if mode == "pause":
                control.pause_point()
            else:
                control.checkpoint()
            if delay:
                time.sleep(delay)
            control.progress(0.5)
            meta = BookMetadata.from_path(path)
            return ExtractionResult(metadata=meta, chapters=[Chapter(text=f"内容-{path}")])

    return SlowExtractor()


@pytest.fixture
def engine_env(monkeypatch):
    listener = FakeListener()
    engine = ConversionEngine(listener, max_workers=2)
    yield listener, engine
    engine.shutdown()


def _wait_batch(listener, timeout=10):
    assert listener.batch_event.wait(timeout), "batch_finished 未触发"
    return [e for e in listener.events if e[0] == "batch"]


class TestEngineBasics:
    def test_success_sequence(self, engine_env, tmp_path, monkeypatch):
        listener, engine = engine_env
        f1 = tmp_path / "a.txt"
        f1.write_text("hello")
        f2 = tmp_path / "b.txt"
        f2.write_text("world")
        monkeypatch.setattr("core.engine.get_extractor", lambda p: _make_extractor())

        out = tmp_path / "out"
        engine.submit([str(f1), str(f2)], ConversionOptions(str(out), "txt"))
        batches = _wait_batch(listener)

        assert batches == [("batch", 2, 2)]
        finished = [e for e in listener.events if e[0] == "finished"]
        assert all(e[2] for e in finished)
        assert all(e[4] == len(f"内容-{p}") for e, p in zip(finished, [str(f1), str(f2)]))
        assert (out / "a.txt").exists() and (out / "b.txt").exists()

    def test_rejects_overlapping_submit(self, engine_env, tmp_path, monkeypatch):
        listener, engine = engine_env
        monkeypatch.setattr("core.engine.get_extractor", lambda p: _make_extractor(delay=0.2))
        f = tmp_path / "a.txt"
        f.write_text("x")
        engine.submit([str(f)], ConversionOptions(str(tmp_path / "o1"), "txt"))
        with pytest.raises(RuntimeError):
            engine.submit([str(f)], ConversionOptions(str(tmp_path / "o2"), "txt"))
        _wait_batch(listener)

    def test_conversion_error_reported(self, engine_env, tmp_path, monkeypatch):
        listener, engine = engine_env

        class BadExtractor:
            def metadata(self, path):
                raise RuntimeError("boom")

            def extract(self, path, control=None):
                raise ValueError("内容损坏")

        monkeypatch.setattr("core.engine.get_extractor", lambda p: BadExtractor())
        f = tmp_path / "bad.txt"
        f.write_text("x")
        engine.submit([str(f)], ConversionOptions(str(tmp_path / "out"), "txt"))
        _wait_batch(listener)
        finished = [e for e in listener.events if e[0] == "finished"]
        assert len(finished) == 1 and finished[0][2] is False
        assert "内容损坏" in finished[0][3]


class TestEngineCancel:
    def test_cancel_running_tasks(self, engine_env, tmp_path, monkeypatch):
        listener, engine = engine_env
        gate = threading.Event()
        monkeypatch.setattr("core.engine.get_extractor", lambda p: _make_extractor(mode="gate", gate=gate))
        f1 = tmp_path / "a.txt"
        f1.write_text("x")
        f2 = tmp_path / "b.txt"
        f2.write_text("x")

        engine.submit([str(f1), str(f2)], ConversionOptions(str(tmp_path / "out"), "txt"))
        assert listener.started.wait(5), "任务未启动"
        time.sleep(0.2)  # 等待 worker 进入 gate 阻塞
        engine.cancel()
        gate.set()  # 放行，worker 在检查点抛出 TaskCancelled

        batches = _wait_batch(listener)
        assert batches == [("batch", 0, 2)]
        finished = [e for e in listener.events if e[0] == "finished"]
        assert len(finished) == 2 and all("取消" in e[3] for e in finished)

    def test_cancel_queued_tasks(self, engine_env, tmp_path, monkeypatch):
        listener, engine = engine_env
        started_first = threading.Event()
        gate = threading.Event()

        class GateExtractor:
            def metadata(self, path):
                return BookMetadata.from_path(path)

            def extract(self, path, control=None):
                control.checkpoint()
                if not started_first.is_set():
                    started_first.set()
                gate.wait(10)
                control.checkpoint()  # 放行后再次检查取消
                control.progress(1.0)
                return ExtractionResult(
                    metadata=BookMetadata.from_path(path), chapters=[Chapter(text="ok")]
                )

        monkeypatch.setattr("core.engine.get_extractor", lambda p: GateExtractor())
        files = [tmp_path / f"f{i}.txt" for i in range(4)]
        for f in files:
            f.write_text("x")
        engine.submit([str(f) for f in files], ConversionOptions(str(tmp_path / "out"), "txt"))

        assert started_first.wait(5)
        engine.cancel()
        gate.set()
        _wait_batch(listener)

        finished = [e for e in listener.events if e[0] == "finished"]
        assert len(finished) == 4
        assert all("取消" in e[3] for e in finished)


class TestEnginePause:
    def test_pause_blocks_then_resume(self, engine_env, tmp_path, monkeypatch):
        listener, engine = engine_env
        gate = threading.Event()
        monkeypatch.setattr("core.engine.get_extractor", lambda p: _make_extractor(mode="pause", gate=gate))
        f = tmp_path / "a.txt"
        f.write_text("x")

        engine.submit([str(f)], ConversionOptions(str(tmp_path / "out"), "txt"))
        assert listener.started.wait(5)
        engine.pause()
        gate.set()  # worker 通过 gate 后应阻塞在 pause_point
        time.sleep(0.3)
        assert not listener.batch_event.is_set(), "暂停期间任务不应完成"

        engine.resume()
        _wait_batch(listener)
        finished = [e for e in listener.events if e[0] == "finished"]
        assert finished and finished[0][2] is True


class TestUniqueOutputPath:
    def test_unique_names_sequentially(self, tmp_path):
        first = unique_output_path(str(tmp_path), "book.txt")
        first.write_text("x")
        second = unique_output_path(str(tmp_path), "book.txt")
        second.write_text("x")
        third = unique_output_path(str(tmp_path), "book.txt")
        assert [p.name for p in (first, second, third)] == ["book.txt", "book (2).txt", "book (3).txt"]
