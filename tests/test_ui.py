"""UI 冒烟测试（QT_QPA_PLATFORM=offscreen）。"""

import sys

import pytest

from core.models import BookMetadata
from ui.file_table_model import FileTableModel


class TestFileTableModel:
    def test_add_and_dedup(self, tmp_path):
        model = FileTableModel()
        f1 = tmp_path / "a.epub"
        f1.write_text("x")
        f2 = tmp_path / "b.pdf"
        f2.write_text("x")
        assert model.add_paths([str(f1), str(f2)]) == 2
        assert model.add_paths([str(f1)]) == 0  # 路径去重
        if sys.platform == "win32":
            # 大小写不敏感去重仅适用于 Windows 文件系统（os.path.normcase 平台语义）
            assert model.add_paths([str(f1).upper()]) == 0
        assert model.paths() == [str(f1), str(f2)]

    def test_clear(self, tmp_path):
        model = FileTableModel()
        f = tmp_path / "a.txt"
        f.write_text("x")
        model.add_paths([str(f)])
        model.clear()
        assert model.rowCount() == 0
        assert model.paths() == []

    def test_metadata_backfill(self, tmp_path):
        model = FileTableModel()
        f = tmp_path / "book.epub"
        f.write_text("x")
        model.add_paths([str(f)])
        meta = BookMetadata(path=str(f), fmt="epub", title="书名", author="作者", chapter_count=3)
        model.update_metadata(str(f), meta)
        assert model.data(model.index(0, 1)) == "书名"
        assert model.data(model.index(0, 2)) == "作者"
        assert model.data(model.index(0, 3)) == "3"
        assert model.data(model.index(0, 4)) == "—"  # 字数待转换后回填

    def test_task_status_and_word_count(self, tmp_path):
        model = FileTableModel()
        f = tmp_path / "book.txt"
        f.write_text("x")
        model.add_paths([str(f)])
        model.mark_queued()
        assert model.data(model.index(0, 5)) == "排队中"
        model.mark_running(str(f))
        assert model.data(model.index(0, 5)) == "转换中…"
        model.mark_finished(str(f), True, "成功转换：book.md", 12345)
        assert model.data(model.index(0, 5)) == "✓ 成功"
        assert model.data(model.index(0, 4)) == "12,345"
        model.mark_finished(str(f), False, "已取消", None)
        assert model.data(model.index(0, 5)) == "已取消"
        model.mark_finished(str(f), False, "转换失败 book.txt： boom", None)
        assert model.data(model.index(0, 5)) == "✗ 失败"

    def test_column_headers(self):
        model = FileTableModel()
        for column, name in enumerate(["文件名", "书名", "作者", "章节数", "字数", "状态"]):
            assert model.headerData(column, __import__("PySide6").QtCore.Qt.Orientation.Horizontal) == name


class TestMainWindowSmoke:
    def test_construct_and_add_files(self, qapp, tmp_path, monkeypatch):
        from ui.main_window import MainWindow
        from ui.settings import SettingsManager

        # 避免冒烟测试污染真实用户设置
        monkeypatch.setattr(SettingsManager, "_save_settings", lambda self, w: None, raising=False)
        monkeypatch.setattr(MainWindow, "_save_settings", lambda self: None)
        monkeypatch.setattr(SettingsManager, "sync", lambda self: None)

        f1 = tmp_path / "sample.txt"
        f1.write_text("你好世界", encoding="utf-8")

        window = MainWindow(SettingsManager())
        assert window.windowTitle().startswith("电子书转换工具")
        added = window._add_files_to_model([str(f1)])
        assert added == 1
        assert window._model.paths() == [str(f1)]
        assert window._model.data(window._model.index(0, 0)) == "sample.txt"
        window.close()
