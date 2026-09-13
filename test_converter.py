#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB转TXT工具 v3.0 环境测试脚本
"""

import sys


def test_imports():
    """测试必要的包是否已安装"""
    missing = []
    for name in ("ebooklib", "bs4", "lxml", "mobi", "chardet", "PySide6", "pypdf", "docx"):
        try:
            __import__(name)
        except ImportError as e:
            missing.append(f"{name} ({e})")
    if missing:
        print("✗ 缺少依赖包:")
        for m in missing:
            print(f"  - {m}")
        print("请运行: pip install -r requirements.txt")
        return False
    print("✓ 所有依赖包已正确安装")
    return True


def test_gui():
    """测试 PySide6 GUI 是否可以启动（offscreen）"""
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance() or QApplication([])
        print("✓ PySide6 GUI 界面支持正常")
        return True
    except Exception as e:
        print(f"✗ GUI 测试失败: {e}")
        return False


def test_core():
    """测试核心转换模块可导入"""
    try:
        from core.engine import ConversionEngine  # noqa: F401
        from core.extractors.registry import get_extractor, SUPPORTED_INPUT_FORMATS  # noqa: F401
        from core.formatters import format_result  # noqa: F401

        print(f"✓ 核心模块正常，支持输入格式：{' '.join(SUPPORTED_INPUT_FORMATS)}")
        return True
    except Exception as e:
        print(f"✗ 核心模块导入失败: {e}")
        return False


def main():
    print("电子书转换工具 v3.0 - 环境测试")
    print("=" * 40)

    if sys.version_info < (3, 10):
        print("✗ Python 版本过低，需要 3.10+（PySide6 要求）")
        return False
    print(f"✓ Python 版本: {sys.version.split()[0]}")

    ok = test_imports() and test_core() and test_gui()

    print("\n" + "=" * 40)
    if ok:
        print("✓ 所有测试通过！")
        print("运行命令: python main.py")
    else:
        print("✗ 存在未通过的项目，请先解决上述问题")
    return ok


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
