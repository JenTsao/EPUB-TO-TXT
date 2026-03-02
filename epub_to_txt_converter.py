#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 转 TXT 工具
支持批量转换 EPUB 文件为 TXT 格式
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re


class EpubToTxtConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("EPUB 转 TXT 工具")
        self.root.geometry("800x600")
        
        # 文件列表
        self.epub_files = []
        self.output_dir = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="选择 EPUB 文件", padding="5")
        file_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="添加文件", command=self.add_files).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(file_frame, text="添加文件夹", command=self.add_folder).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="清空列表", command=self.clear_files).grid(row=0, column=2, padx=(5, 0))
        
        # 输出目录选择
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="5")
        output_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="输出目录:").grid(row=0, column=0, sticky=tk.W)
        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(output_frame, text="选择", command=self.select_output_dir).grid(row=0, column=2)
        
        # 文件列表和日志区域
        list_frame = ttk.LabelFrame(main_frame, text="文件列表", padding="5")
        list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 文件列表
        self.file_listbox = tk.Listbox(list_frame, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(1, weight=1)
        
        ttk.Label(progress_frame, text="进度:").grid(row=0, column=0, sticky=tk.W)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.grid(row=0, column=2)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 设置默认输出目录
        default_output = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(default_output):
            default_output = os.path.expanduser("~")
        self.output_var.set(default_output)
        
    def add_files(self):
        """添加 EPUB 文件"""
        files = filedialog.askopenfilenames(
            title="选择 EPUB 文件",
            filetypes=[("EPUB files", "*.epub"), ("All files", "*.*")]
        )
        
        added_count = 0
        for file in files:
            abs_path = os.path.abspath(file)
            if abs_path not in [os.path.abspath(f) for f in self.epub_files]:
                self.epub_files.append(abs_path)
                self.file_listbox.insert(tk.END, os.path.basename(file))
                added_count += 1
        
        self.log(f"添加了 {added_count} 个文件")
    
    def add_folder(self):
        """添加文件夹中的所有 EPUB 文件"""
        folder = filedialog.askdirectory(title="选择包含 EPUB 文件的文件夹")
        if not folder:
            return
            
        epub_files = list(Path(folder).glob("*.epub"))
        added_count = 0
        
        existing_paths = [os.path.abspath(f) for f in self.epub_files]
        for file in epub_files:
            file_str = os.path.abspath(str(file))
            if file_str not in existing_paths:
                self.epub_files.append(file_str)
                self.file_listbox.insert(tk.END, file.name)
                added_count += 1
                existing_paths.append(file_str)
        
        self.log(f"从文件夹添加了 {added_count} 个 EPUB 文件")
    
    def clear_files(self):
        """清空文件列表"""
        self.epub_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.log("已清空文件列表")
    
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_var.set(directory)
            self.log(f"输出目录设置为：{directory}")
    
    def log(self, message):
        """添加日志信息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def extract_text_from_epub(self, epub_path):
        """从 EPUB 文件提取文本内容"""
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                book = epub.read_epub(epub_path)
            text_content = []
            
            title = book.get_metadata('DC', 'title')
            author = book.get_metadata('DC', 'creator')
            
            if title:
                text_content.append(f"书名：{title[0][0]}")
            if author:
                text_content.append(f"作者：{author[0][0]}")
            text_content.append("-" * 50)
            text_content.append("")
            
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_DOCUMENT:
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    text = soup.get_text()
                    
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    if text.strip():
                        text_content.append(text)
                        text_content.append("")
            
            return '\n'.join(text_content)
            
        except Exception as e:
            self.log(f"错误详情：{str(e)}")
            raise Exception(f"处理 EPUB 文件 {os.path.basename(epub_path)} 时出错：{str(e)}")
    
    def convert_single_file(self, epub_path, output_dir):
        """转换单个 EPUB 文件"""
        try:
            # 提取文本
            text_content = self.extract_text_from_epub(epub_path)
            
            # 生成输出文件名
            epub_name = Path(epub_path).stem
            txt_path = os.path.join(output_dir, f"{epub_name}.txt")
            
            # 写入文本文件
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            return True, f"成功转换：{epub_name}.txt"
            
        except Exception as e:
            return False, f"转换失败 {os.path.basename(epub_path)}: {str(e)}"
    
    def start_conversion(self):
        """开始转换过程"""
        if not self.epub_files:
            messagebox.showwarning("警告", "请先添加 EPUB 文件")
            return
        
        if not self.output_var.get():
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        # 在新线程中执行转换
        threading.Thread(target=self.convert_files, daemon=True).start()
    
    def convert_files(self):
        """转换所有文件"""
        output_dir = self.output_var.get()
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 禁用转换按钮
        self.convert_button.config(state=tk.DISABLED)
        
        # 设置进度条
        total_files = len(self.epub_files)
        self.progress['maximum'] = total_files
        self.progress['value'] = 0
        
        success_count = 0
        
        for i, epub_file in enumerate(self.epub_files):
            self.log(f"正在转换：{os.path.basename(epub_file)}")
            
            success, message = self.convert_single_file(epub_file, output_dir)
            self.log(message)
            
            if success:
                success_count += 1
            
            # 更新进度
            self.progress['value'] = i + 1
            self.progress_label.config(text=f"{i + 1}/{total_files}")
            self.root.update_idletasks()
        
        # 转换完成
        self.log(f"转换完成！成功：{success_count}/{total_files}")
        self.convert_button.config(state=tk.NORMAL)
        
        # 重置进度条
        self.progress['value'] = 0
        self.progress_label.config(text="0/0")
        
        messagebox.showinfo("完成", f"转换完成!\n成功转换：{success_count}/{total_files} 个文件")


def main():
    root = tk.Tk()
    app = EpubToTxtConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
