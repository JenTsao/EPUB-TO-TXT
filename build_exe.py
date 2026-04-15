#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电子书转换工具 v2.0 打包脚本
使用 PyInstaller 将 Python 程序打包成 exe 文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理目录: {dir_name}")
    
    # 清理 spec 文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"已清理文件: {spec_file}")

def build_exe():
    """构建 exe 文件"""
    print("开始构建电子书转换工具 v2.0...")
    
    # PyInstaller 命令参数
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=电子书转换工具',
        '--icon=icon.ico',
        '--add-data=README.md;.',
        '--add-data=发布说明.md;.',
        '--hidden-import=ebooklib',
        '--hidden-import=bs4',
        '--hidden-import=lxml',
        '--hidden-import=mobi',
        '--hidden-import=chardet',
        '--hidden-import=tkinterdnd2',
        '--clean',
        'epub_to_txt_converter.py'
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists('icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ 打包成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_icon():
    """创建简单的图标文件"""
    try:
        from PIL import Image, ImageDraw
        
        img = Image.new('RGBA', (64, 64), (70, 130, 180, 255))
        draw = ImageDraw.Draw(img)
        
        draw.rectangle([10, 15, 54, 50], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        draw.rectangle([10, 15, 15, 50], fill=(200, 200, 200, 255))
        for y in range(20, 45, 4):
            draw.line([18, y, 50, y], fill=(150, 150, 150, 255))
        
        img.save('icon.ico', format='ICO')
        print("✓ 已创建图标文件")
        return True
    except ImportError:
        print("! 未安装 PIL 库，跳过图标创建")
        return False

def post_build_cleanup():
    """构建后清理"""
    exe_path = Path('dist/电子书转换工具.exe')
    if exe_path.exists():
        target_path = Path('./电子书转换工具.exe')
        if target_path.exists():
            target_path.unlink()
        shutil.move(str(exe_path), str(target_path))
        print(f"✓ exe 文件已移动到: {target_path}")
    
    # 清理构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # 清理 spec 文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()

def main():
    print("电子书转换工具 v2.0 - 打包脚本")
    print("=" * 40)
    
    try:
        import PyInstaller
        print(f"✓ PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("✗ 未安装 PyInstaller，请运行: pip install pyinstaller")
        return False
    
    clean_build()
    create_icon()
    
    if build_exe():
        post_build_cleanup()
        print("\n" + "=" * 40)
        print("✓ 打包完成！")
        print("生成的文件: 电子书转换工具.exe")
        print("可以直接运行该 exe 文件，无需安装 Python 环境")
        return True
    else:
        print("\n" + "=" * 40)
        print("✗ 打包失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
