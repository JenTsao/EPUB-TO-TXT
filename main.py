#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""电子书转换工具 v3.0 入口：装配 QApplication、主题与主窗口。"""

import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.settings import SettingsManager, ThemeManager


def run() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("EbookConverter")
    app.setOrganizationName("EbookConverter")

    settings = SettingsManager()
    ThemeManager.apply(app, settings.theme)

    window = MainWindow(settings)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
