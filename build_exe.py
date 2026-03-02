#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB转TXT工具打包脚本
使用PyInstaller将Python程序打包成exe文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def clean_build():
    """清理之前的构建文件"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理目录: {dir_name}")
    
    # 清理spec文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"已清理文件: {spec_file}")

def build_exe():
    """构建exe文件"""
    print("开始构建EPUB转TXT工具...")
    
    # PyInstaller命令参数
    cmd = [
        'pyinstaller',
        '--onefile',                    # 打包成单个exe文件
        '--windowed',                   # 不显示控制台窗口
        '--name=EPUB转TXT工具',          # 设置exe文件名
        '--icon=icon.ico',              # 图标文件（如果存在）
        '--add-data=README.md;.',       # 包含说明文件
        '--hidden-import=ebooklib',     # 确保导入ebooklib
        '--hidden-import=bs4',          # 确保导入beautifulsoup4
        '--hidden-import=lxml',         # 确保导入lxml
        '--clean',                      # 清理临时文件
        'epub_to_txt_converter.py'      # 主程序文件
    ]
    
    # 如果没有图标文件，移除图标参数
    if not os.path.exists('icon.ico'):
        cmd = [arg for arg in cmd if not arg.startswith('--icon')]
    
    try:
        # 执行打包命令
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
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建64x64的图标
        img = Image.new('RGBA', (64, 64), (70, 130, 180, 255))  # 钢蓝色背景
        draw = ImageDraw.Draw(img)
        
        # 绘制简单的书本图标
        # 书本外框
        draw.rectangle([10, 15, 54, 50], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        # 书脊
        draw.rectangle([10, 15, 15, 50], fill=(200, 200, 200, 255))
        # 页面线条
        for y in range(20, 45, 4):
            draw.line([18, y, 50, y], fill=(150, 150, 150, 255))
        
        # 保存为ico文件
        img.save('icon.ico', format='ICO')
        print("✓ 已创建图标文件")
        return True
    except ImportError:
        print("! 未安装PIL库，跳过图标创建")
        return False

def post_build_cleanup():
    """构建后清理"""
    # 移动exe文件到根目录
    exe_path = Path('dist/EPUB转TXT工具.exe')
    if exe_path.exists():
        target_path = Path('./EPUB转TXT工具.exe')
        if target_path.exists():
            target_path.unlink()
        shutil.move(str(exe_path), str(target_path))
        print(f"✓ exe文件已移动到: {target_path}")
    
    # 清理构建文件
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    # 清理spec文件
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()

def main():
    print("EPUB转TXT工具 - 打包脚本")
    print("=" * 40)
    
    # 检查依赖
    try:
        import PyInstaller
        print(f"✓ PyInstaller版本: {PyInstaller.__version__}")
    except ImportError:
        print("✗ 未安装PyInstaller，请运行: pip install pyinstaller")
        return False
    
    # 清理之前的构建
    clean_build()
    
    # 创建图标（可选）
    create_icon()
    
    # 构建exe
    if build_exe():
        post_build_cleanup()
        print("\n" + "=" * 40)
        print("✓ 打包完成！")
        print("生成的文件: EPUB转TXT工具.exe")
        print("可以直接运行该exe文件，无需安装Python环境")
        return True
    else:
        print("\n" + "=" * 40)
        print("✗ 打包失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)