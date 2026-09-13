#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""QSettings 持久化封装与明暗主题管理（Fusion + 自定义 QPalette，无第三方依赖）。"""

from pathlib import Path

from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import QSettings

_THEME_LIGHT = "light"
_THEME_DARK = "dark"


class SettingsManager:
    """所有持久化设置的读写入口（IniFormat，位于 %APPDATA%/EbookConverter/）。"""

    def __init__(self):
        QSettings.setDefaultFormat(QSettings.IniFormat)
        self._s = QSettings("EbookConverter", "EbookConverter")

    # 输出目录
    @property
    def output_dir(self) -> str:
        default = Path.home() / "Desktop"
        if not default.exists():
            default = Path.home()
        return self._s.value("output_dir", str(default))

    @output_dir.setter
    def output_dir(self, value: str) -> None:
        self._s.setValue("output_dir", value)

    # 输出格式
    @property
    def output_format(self) -> str:
        return self._s.value("output_format", "txt")

    @output_format.setter
    def output_format(self, value: str) -> None:
        self._s.setValue("output_format", value)

    # 主题
    @property
    def theme(self) -> str:
        return self._s.value("theme", _THEME_LIGHT)

    @theme.setter
    def theme(self, value: str) -> None:
        self._s.setValue("theme", value)

    # 文件对话框上次目录
    @property
    def last_browse_dir(self) -> str:
        return self._s.value("last_browse_dir", "")

    @last_browse_dir.setter
    def last_browse_dir(self, value: str) -> None:
        self._s.setValue("last_browse_dir", value)

    # 主窗口几何信息
    def save_geometry(self, main_window) -> None:
        self._s.setValue("geometry", main_window.saveGeometry())

    def restore_geometry(self, main_window) -> None:
        geometry = self._s.value("geometry")
        if isinstance(geometry, bytes) or isinstance(geometry, bytearray):
            main_window.restoreGeometry(bytes(geometry))
        elif geometry is not None:
            main_window.restoreGeometry(geometry)

    def sync(self) -> None:
        self._s.sync()


def _dark_palette() -> QPalette:
    """Qt 官方 Fusion 暗色配色。"""
    palette = QPalette()
    window = QColor(53, 53, 53)
    window_text = QColor(255, 255, 255)
    base = QColor(25, 25, 25)
    alternate = QColor(53, 53, 53)
    tool_tip_base = QColor(53, 53, 53)
    tool_tip_text = QColor(255, 255, 255)
    text = QColor(255, 255, 255)
    button = QColor(53, 53, 53)
    button_text = QColor(255, 255, 255)
    bright_text = QColor(255, 0, 0)
    link = QColor(42, 130, 218)
    highlight = QColor(42, 130, 218)
    highlighted_text = QColor(255, 255, 255)
    disabled = QColor(127, 127, 127)

    for role, color in [
        (QPalette.ColorRole.Window, window),
        (QPalette.ColorRole.WindowText, window_text),
        (QPalette.ColorRole.Base, base),
        (QPalette.ColorRole.AlternateBase, alternate),
        (QPalette.ColorRole.ToolTipBase, tool_tip_base),
        (QPalette.ColorRole.ToolTipText, tool_tip_text),
        (QPalette.ColorRole.Text, text),
        (QPalette.ColorRole.Button, button),
        (QPalette.ColorRole.ButtonText, button_text),
        (QPalette.ColorRole.BrightText, bright_text),
        (QPalette.ColorRole.Link, link),
        (QPalette.ColorRole.Highlight, highlight),
        (QPalette.ColorRole.HighlightedText, highlighted_text),
        (QPalette.ColorRole.PlaceholderText, disabled),
    ]:
        palette.setColor(role, color)
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        palette.setColor(QPalette.ColorGroup.Disabled, role, disabled)
    return palette


class ThemeManager:
    @staticmethod
    def apply(app, theme: str) -> None:
        app.setStyle("Fusion")
        if theme == _THEME_DARK:
            app.setPalette(_dark_palette())
        else:
            app.setPalette(app.style().standardPalette())

    @staticmethod
    def themes() -> list[tuple[str, str]]:
        return [(_THEME_LIGHT, "浅色"), (_THEME_DARK, "深色")]
