#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兼容入口：v3.0 起代码已拆分为 core/（转换逻辑）与 ui/（PySide6 界面），
此文件仅保留旧版启动方式，实际入口为 main.py。"""

from main import run

if __name__ == "__main__":
    run()
