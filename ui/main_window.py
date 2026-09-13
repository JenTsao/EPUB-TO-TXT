#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PySide6 主窗口：原生拖拽、元信息表格、转换队列控制、设置持久化。"""

import os
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QTableView,
    QWidget,
)

from core.engine import ConversionEngine, ConversionOptions
from core.extractors.registry import INPUT_FILE_FILTER, SUPPORTED_OUTPUT_FORMATS

from .engine_bridge import EngineBridge
from .file_table_model import FileTableModel
from .metadata_worker import MetadataLoader
from .settings import SettingsManager, ThemeManager

APP_TITLE = "电子书转换工具 v3.0"


class MainWindow(QMainWindow):
    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self._settings = settings

        self._bridge = EngineBridge()
        self._engine = ConversionEngine(self._bridge)
        self._meta_loader = MetadataLoader()
        self._model = FileTableModel()
        self._paused = False
        self._done_count = 0
        self._total_count = 0
        self._success_count = 0

        self._bridge.task_started.connect(self._on_task_started)
        self._bridge.task_progress.connect(self._on_task_progress)
        self._bridge.task_finished.connect(self._on_task_finished)
        self._bridge.batch_finished.connect(self._on_batch_finished)
        self._meta_loader.metadata_ready.connect(self._on_metadata_ready)

        self._build_ui()
        self._restore_settings()
        self._update_button_states()

    # ---------------- UI 构建 ----------------
    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root = QGridLayout(central)
        root.setContentsMargins(10, 10, 10, 10)

        # 文件操作
        file_bar = QHBoxLayout()
        self.btn_add_files = QPushButton("添加文件")
        self.btn_add_files.clicked.connect(self.add_files)
        self.btn_add_folder = QPushButton("添加文件夹")
        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_clear = QPushButton("清空列表")
        self.btn_clear.clicked.connect(self.clear_files)
        file_bar.addWidget(self.btn_add_files)
        file_bar.addWidget(self.btn_add_folder)
        file_bar.addWidget(self.btn_clear)
        file_bar.addStretch(1)
        self.lbl_hint = QLabel("提示：支持拖拽文件或文件夹到窗口")
        self.lbl_hint.setStyleSheet("color: gray;")
        file_bar.addWidget(self.lbl_hint)
        root.addLayout(file_bar, 0, 0, 1, 2)

        # 输出设置
        out_bar = QGridLayout()
        out_bar.addWidget(QLabel("输出目录："), 0, 0)
        self.edt_output = QLineEdit()
        out_bar.addWidget(self.edt_output, 0, 1)
        self.btn_browse = QPushButton("浏览…")
        self.btn_browse.clicked.connect(self.browse_output)
        out_bar.addWidget(self.btn_browse, 0, 2)
        self.btn_open_dir = QPushButton("打开目录")
        self.btn_open_dir.clicked.connect(self.open_output_dir)
        out_bar.addWidget(self.btn_open_dir, 0, 3)
        out_bar.addWidget(QLabel("输出格式："), 1, 0)
        self.cmb_format = QComboBox()
        for fmt in SUPPORTED_OUTPUT_FORMATS:
            self.cmb_format.addItem(fmt.upper(), fmt)
        self.cmb_format.currentIndexChanged.connect(self._on_format_changed)
        out_bar.addWidget(self.cmb_format, 1, 1)
        out_bar.addWidget(QLabel("主题："), 1, 2, Qt.AlignmentFlag.AlignRight)
        self.cmb_theme = QComboBox()
        for value, label in ThemeManager.themes():
            self.cmb_theme.addItem(label, value)
        self.cmb_theme.currentIndexChanged.connect(self._on_theme_changed)
        out_bar.addWidget(self.cmb_theme, 1, 3)
        out_bar.setColumnStretch(1, 1)
        root.addLayout(out_bar, 1, 0, 1, 2)

        # 文件表格
        self.table = QTableView()
        self.table.setModel(self._model)
        self.table.setAcceptDrops(False)  # 拖拽统一由窗口处理
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 220)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 2, 0, 1, 2)

        # 进度
        progress_bar = QHBoxLayout()
        progress_bar.addWidget(QLabel("进度："))
        self.progress = QProgressBar()
        self.progress.setValue(0)
        progress_bar.addWidget(self.progress, 1)
        self.lbl_counter = QLabel("0/0")
        progress_bar.addWidget(self.lbl_counter)
        self.lbl_status = QLabel("就绪")
        progress_bar.addWidget(self.lbl_status)
        root.addLayout(progress_bar, 3, 0, 1, 2)

        # 控制按钮
        control_bar = QHBoxLayout()
        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.clicked.connect(self.start_conversion)
        self.btn_pause = QPushButton("暂停")
        self.btn_pause.clicked.connect(self.pause_conversion)
        self.btn_resume = QPushButton("继续")
        self.btn_resume.clicked.connect(self.resume_conversion)
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.cancel_conversion)
        control_bar.addWidget(self.btn_convert)
        control_bar.addWidget(self.btn_pause)
        control_bar.addWidget(self.btn_resume)
        control_bar.addWidget(self.btn_cancel)
        control_bar.addStretch(1)
        root.addLayout(control_bar, 4, 0, 1, 2)

        # 日志
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setPlaceholderText("转换日志")
        root.addWidget(self.log_view, 5, 0, 1, 2)

    # ---------------- 设置持久化 ----------------
    def _restore_settings(self) -> None:
        self._settings.restore_geometry(self)
        self.edt_output.setText(self._settings.output_dir)
        index = self.cmb_format.findData(self._settings.output_format)
        if index >= 0:
            self.cmb_format.setCurrentIndex(index)
        theme_index = self.cmb_theme.findData(self._settings.theme)
        if theme_index >= 0:
            self.cmb_theme.blockSignals(True)
            self.cmb_theme.setCurrentIndex(theme_index)
            self.cmb_theme.blockSignals(False)

    def _save_settings(self) -> None:
        self._settings.output_dir = self.edt_output.text().strip()
        self._settings.output_format = self.cmb_format.currentData() or "txt"
        self._settings.save_geometry(self)
        self._settings.sync()

    def closeEvent(self, event) -> None:
        if self._engine.is_running:
            self._engine.cancel()
        self._save_settings()
        self._meta_loader.shutdown()
        super().closeEvent(event)

    # ---------------- 拖拽 ----------------
    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        files: list[str] = []
        folders: list[str] = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if not path:
                continue
            if os.path.isdir(path):
                folders.append(path)
            elif os.path.splitext(path)[1].lower() in self._supported_extensions():
                files.append(path)
            else:
                self.log(f"不支持的格式：{os.path.splitext(path)[1]}")
        added = self._add_files_to_model(files)
        for folder in folders:
            added += self._scan_folder(folder)
        if added:
            self.log(f"拖拽添加了 {added} 个文件")
        event.acceptProposedAction()

    @staticmethod
    def _supported_extensions() -> set[str]:
        from core.extractors.registry import SUPPORTED_INPUT_FORMATS

        return set(SUPPORTED_INPUT_FORMATS)

    def _scan_folder(self, folder: str) -> int:
        found: list[str] = []
        for ext in self._supported_extensions():
            for file in Path(folder).rglob(f"*{ext}"):
                found.append(str(file))
        return self._add_files_to_model(found)

    def _add_files_to_model(self, paths: list[str]) -> int:
        added = self._model.add_paths(paths)
        if added:
            # 元信息请求由 MetadataLoader 按 path 去重，重复请求不会重复解析
            for path in paths:
                self._meta_loader.request(path)
        return added

    # ---------------- 文件操作 ----------------
    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择文件", self._settings.last_browse_dir or "", INPUT_FILE_FILTER
        )
        if not files:
            return
        self._settings.last_browse_dir = os.path.dirname(files[0])
        added = self._add_files_to_model(files)
        if added:
            self.log(f"添加了 {added} 个文件")

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", self._settings.last_browse_dir or "")
        if not folder:
            return
        self._settings.last_browse_dir = folder
        count = self._scan_folder(folder)
        self.log(f"从文件夹添加了 {count} 个文件")

    def clear_files(self) -> None:
        self._model.clear()
        self.log("已清空文件列表")

    def browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录", self.edt_output.text().strip())
        if directory:
            self.edt_output.setText(directory)

    def open_output_dir(self) -> None:
        output_dir = self.edt_output.text().strip()
        if output_dir and Path(output_dir).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))

    # ---------------- 转换控制 ----------------
    def start_conversion(self) -> None:
        paths = self._model.paths()
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加文件")
            return
        output_dir = self.edt_output.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "警告", "请选择输出目录")
            return

        options = ConversionOptions(output_dir, self.cmb_format.currentData() or "txt")
        self._done_count = 0
        self._total_count = len(paths)
        self._success_count = 0
        self._paused = False
        self._model.mark_queued()
        self.progress.setMaximum(self._total_count)
        self.progress.setValue(0)
        self.lbl_counter.setText(f"0/{self._total_count}")
        self.lbl_status.setText("转换中…")
        self._update_button_states()
        self._engine.submit(paths, options)

    def pause_conversion(self) -> None:
        self._engine.pause()
        self._paused = True
        self.lbl_status.setText("已暂停")
        self._update_button_states()

    def resume_conversion(self) -> None:
        self._engine.resume()
        self._paused = False
        self.lbl_status.setText("转换中…")
        self._update_button_states()

    def cancel_conversion(self) -> None:
        self._engine.cancel()
        self.lbl_status.setText("正在取消…")
        self._update_button_states()

    def _update_button_states(self) -> None:
        running = self._engine.is_running
        self.btn_convert.setEnabled(not running)
        self.btn_add_files.setEnabled(not running)
        self.btn_add_folder.setEnabled(not running)
        self.btn_clear.setEnabled(not running)
        self.btn_pause.setEnabled(running and not self._paused)
        self.btn_resume.setEnabled(running and self._paused)
        self.btn_cancel.setEnabled(running)

    # ---------------- 引擎事件槽 ----------------
    def _on_task_started(self, path: str) -> None:
        self._model.mark_running(path)
        self.log(f"正在处理：{os.path.basename(path)} …")

    def _on_task_progress(self, path: str, ratio: float, message: str) -> None:
        if message:
            self.log(f"{os.path.basename(path)}：{message}")

    def _on_task_finished(self, path: str, ok: bool, message: str, word_count) -> None:
        self._model.mark_finished(path, ok, message, word_count)
        self._done_count += 1
        if ok:
            self._success_count += 1
        self.progress.setValue(self._done_count)
        self.lbl_counter.setText(f"{self._done_count}/{self._total_count}")
        self.log(message)

    def _on_batch_finished(self, success_count: int, total: int) -> None:
        self._update_button_states()
        self.lbl_status.setText("完成")
        self.log(f"全部任务结束！成功：{success_count}/{total}")
        answer = QMessageBox.question(
            self,
            "完成",
            f"转换完成！\n成功转换：{success_count}/{total} 个文件\n\n是否打开输出目录？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.open_output_dir()

    def _on_metadata_ready(self, path: str, meta) -> None:
        self._model.update_metadata(path, meta)

    # ---------------- 选项变化 ----------------
    def _on_format_changed(self) -> None:
        pass  # 格式随提交时读取，无需即时处理

    def _on_theme_changed(self) -> None:
        theme = self.cmb_theme.currentData()
        if theme:
            self._settings.theme = theme
            from PySide6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                ThemeManager.apply(app, theme)

    # ---------------- 日志 ----------------
    def log(self, message: str) -> None:
        self.log_view.appendPlainText(message)
