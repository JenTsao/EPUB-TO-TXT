#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件列表表格模型：文件名/书名/作者/章节数/字数/状态，支持异步元信息回填。"""

import os
from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from core.models import BookMetadata


@dataclass
class FileRow:
    path: str
    title: str = ""
    author: str = ""
    chapter_count: int | None = None
    word_count: int | None = None
    status: str = ""


_COLUMNS = ["文件名", "书名", "作者", "章节数", "字数", "状态"]

_STATUS_QUEUED = "排队中"
_STATUS_RUNNING = "转换中…"
_STATUS_OK = "✓ 成功"
_STATUS_CANCELLED = "已取消"
_STATUS_FAILED = "✗ 失败"


class FileTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[FileRow] = []
        self._keys: set[str] = set()  # 归一化绝对路径，用于去重

    # ---- Qt 模型接口 ----
    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()):
        return len(_COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return _COLUMNS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            column = index.column()
            if column == 0:
                return os.path.basename(row.path)
            if column == 1:
                return row.title or "—"
            if column == 2:
                return row.author or "—"
            if column == 3:
                return str(row.chapter_count) if row.chapter_count is not None else "—"
            if column == 4:
                return f"{row.word_count:,}" if row.word_count is not None else "—"
            if column == 5:
                return row.status
        elif role == Qt.ItemDataRole.ToolTipRole:
            return row.path
        return None

    # ---- 数据操作 ----
    @staticmethod
    def _key(path: str) -> str:
        return os.path.normcase(os.path.abspath(path))

    def add_paths(self, paths: list[str]) -> int:
        """批量添加，按绝对路径去重，返回实际新增数量。"""
        added = []
        for path in paths:
            key = self._key(path)
            if key in self._keys:
                continue
            self._keys.add(key)
            added.append(FileRow(path=path))
        if not added:
            return 0
        first = len(self._rows)
        last = first + len(added) - 1
        self.beginInsertRows(QModelIndex(), first, last)
        self._rows.extend(added)
        self.endInsertRows()
        return len(added)

    def clear(self) -> None:
        self.beginResetModel()
        self._rows.clear()
        self._keys.clear()
        self.endResetModel()

    def paths(self) -> list[str]:
        return [row.path for row in self._rows]

    def _row_index(self, path: str) -> int | None:
        key = self._key(path)
        for i, row in enumerate(self._rows):
            if self._key(row.path) == key:
                return i
        return None

    def _update_row(self, path: str, mutate) -> None:
        index = self._row_index(path)
        if index is None:
            return
        mutate(self._rows[index])
        self.dataChanged.emit(self.index(index, 0), self.index(index, len(_COLUMNS) - 1))

    def update_metadata(self, path: str, meta: BookMetadata) -> None:
        """后台元信息线程回填。"""

        def apply(row: FileRow) -> None:
            row.title = meta.title or ""
            row.author = meta.author or ""
            row.chapter_count = meta.chapter_count

        self._update_row(path, apply)

    def mark_queued(self) -> None:
        for i, row in enumerate(self._rows):
            row.status = _STATUS_QUEUED
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._rows) - 1, len(_COLUMNS) - 1))

    def mark_running(self, path: str) -> None:
        self._update_row(path, lambda row: setattr(row, "status", _STATUS_RUNNING))

    def mark_finished(self, path: str, ok: bool, message: str, word_count: int | None) -> None:
        def apply(row: FileRow) -> None:
            if ok:
                row.status = _STATUS_OK
                if word_count is not None:
                    row.word_count = word_count
            elif "取消" in message:
                row.status = _STATUS_CANCELLED
            else:
                row.status = _STATUS_FAILED

        self._update_row(path, apply)
