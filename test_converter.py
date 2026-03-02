#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB转TXT工具测试脚本
"""

import os
import sys
from pathlib import Path

def test_imports():
    """测试必要的包是否已安装"""
    try:
        import ebooklib
        import bs4
        import lxml
        print("✓ 所有依赖包已正确安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖包: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def test_gui():
    """测试GUI是否可以启动"""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        root.destroy()
        print("✓ GUI界面支持正常")
        return True
    except Exception as e:
        print(f"✗ GUI测试失败: {e}")
        return False

def main():
    print("EPUB转TXT工具 - 环境测试")
    print("=" * 40)
    
    # 检查Python版本
    if sys.version_info < (3, 6):
        print("✗ Python版本过低，需要3.6+")
        return False
    else:
        print(f"✓ Python版本: {sys.version.split()[0]}")
    
    # 测试依赖包
    if not test_imports():
        return False
    
    # 测试GUI
    if not test_gui():
        return False
    
    print("\n" + "=" * 40)
    print("✓ 所有测试通过！可以正常使用EPUB转TXT工具")
    print("运行命令: python epub_to_txt_converter.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)