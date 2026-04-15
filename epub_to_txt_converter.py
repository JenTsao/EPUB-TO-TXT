#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB 转 TXT 工具 v2.0
支持批量转换电子书为多种格式
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import threading
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import chardet
import gc

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_SUPPORTED = True
except ImportError:
    DND_SUPPORTED = False


SUPPORTED_INPUT_FORMATS = ['.epub', '.mobi', '.txt', '.html', '.htm']
SUPPORTED_OUTPUT_FORMATS = ['txt', 'md', 'html']


class EbookConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("电子书转 TXT 工具 v2.0")
        self.root.geometry("900x650")
        
        self.files = []
        self.output_format = tk.StringVar(value='txt')
        self.converting = False
        
        self.setup_ui()
        if DND_SUPPORTED:
            self.setup_drag_drop()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        file_frame = ttk.LabelFrame(main_frame, text="选择文件", padding="5")
        file_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="添加文件", command=self.add_files).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(file_frame, text="添加文件夹", command=self.add_folder).grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Button(file_frame, text="清空列表", command=self.clear_files).grid(row=0, column=2, padx=(5, 0))
        
        drag_hint = "提示：支持拖拽文件或文件夹到窗口"
        if not DND_SUPPORTED:
            drag_hint += " (需安装 tkinterdnd2)"
        ttk.Label(file_frame, text=drag_hint, foreground="gray").grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        output_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="5")
        output_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        output_frame.columnconfigure(1, weight=1)
        
        ttk.Label(output_frame, text="输出目录：").grid(row=0, column=0, sticky=tk.W)
        self.output_var = tk.StringVar()
        ttk.Entry(output_frame, textvariable=self.output_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(output_frame, text="选择", command=self.select_output_dir).grid(row=0, column=2)
        
        ttk.Label(output_frame, text="输出格式：").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        format_frame = ttk.Frame(output_frame)
        format_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        ttk.Radiobutton(format_frame, text="TXT", variable=self.output_format, value='txt').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="Markdown (MD)", variable=self.output_format, value='md').pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="HTML", variable=self.output_format, value='html').pack(side=tk.LEFT)
        
        list_frame = ttk.LabelFrame(main_frame, text="文件列表", padding="5")
        list_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(list_frame, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(1, weight=1)
        
        ttk.Label(progress_frame, text="进度：").grid(row=0, column=0, sticky=tk.W)
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.grid(row=0, column=2)
        
        self.status_label = ttk.Label(progress_frame, text="就绪")
        self.status_label.grid(row=0, column=3, padx=(10, 0))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=4, pady=(0, 10))
        
        self.convert_button = ttk.Button(button_frame, text="开始转换", command=self.start_conversion)
        self.convert_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT)
        
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        default_output = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(default_output):
            default_output = os.path.expanduser("~")
        self.output_var.set(default_output)
        
    def setup_drag_drop(self):
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.handle_drop)
        
    def handle_drop(self, event):
        files = self.root.tk.splitlist(event.data)
        added_count = 0
        
        for path in files:
            path = path.strip('{}')
            if os.path.isdir(path):
                added = self.add_folder_files(path)
                added_count += added
            elif os.path.isfile(path):
                ext = Path(path).suffix.lower()
                if ext in SUPPORTED_INPUT_FORMATS:
                    if self.add_single_file(path):
                        added_count += 1
                else:
                    self.log(f"不支持的格式：{ext}")
        
        if added_count > 0:
            self.log(f"拖拽添加了 {added_count} 个文件")
    
    def add_folder_files(self, folder_path):
        count = 0
        for ext in SUPPORTED_INPUT_FORMATS:
            for file in Path(folder_path).rglob(f"*{ext}"):
                if self.add_single_file(str(file)):
                    count += 1
        return count
    
    def add_single_file(self, file_path):
        abs_path = os.path.abspath(file_path)
        # 检查文件是否已存在（大小写不敏感）
        existing_paths = [os.path.abspath(f).lower() for f in self.files]
        if abs_path.lower() not in existing_paths:
            self.files.append(abs_path)
            self.file_listbox.insert(tk.END, os.path.basename(file_path))
            return True
        return False
        
    def add_files(self):
        filetypes = [
            ("电子书文件", "*.epub *.mobi *.txt *.html *.htm"),
            ("所有文件", "*.*")
        ]
        files = filedialog.askopenfilenames(title="选择文件", filetypes=filetypes)
        
        added = 0
        for file in files:
            if self.add_single_file(file):
                added += 1
        
        if added > 0:
            self.log(f"添加了 {added} 个文件")
    
    def add_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            count = self.add_folder_files(folder)
            self.log(f"从文件夹添加了 {count} 个文件")
    
    def clear_files(self):
        self.files.clear()
        self.file_listbox.delete(0, tk.END)
        self.log("已清空文件列表")
    
    def select_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_var.set(directory)
            self.log(f"输出目录设置为：{directory}")
    
    def log(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def detect_encoding(self, data):
        result = chardet.detect(data)
        encoding = result['encoding']
        
        # 常见编码别名处理
        encoding_map = {
            'gb2312': 'gb18030',
            'gbk': 'gb18030',
            'ascii': 'utf-8',
            'iso-8859-1': 'utf-8'
        }
        
        if encoding:
            encoding = encoding.lower()
            if encoding in encoding_map:
                return encoding_map[encoding]
            return encoding
        return 'utf-8'
    
    def extract_text_from_file(self, file_path):
        ext = Path(file_path).suffix.lower()
        
        if ext == '.epub':
            return self.extract_from_epub(file_path)
        elif ext == '.mobi':
            return self.extract_from_mobi(file_path)
        elif ext == '.txt':
            return self.extract_from_txt(file_path)
        elif ext in ['.html', '.htm']:
            return self.extract_from_html(file_path)
        else:
            raise ValueError(f"不支持的格式：{ext}")
    
    def extract_from_epub(self, epub_path):
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
        text_content.append("=" * 50)
        text_content.append("")
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                
                for script in soup(["script", "style"]):
                    script.decompose()
                
                text = soup.get_text()
                text = self.clean_text(text)
                
                if text.strip():
                    text_content.append(text)
                    text_content.append("")
        
        gc.collect()
        return '\n'.join(text_content)
    
    def extract_from_mobi(self, mobi_path):
        try:
            import mobi
            has_mobi_lib = True
        except ImportError:
            has_mobi_lib = False
            self.log("警告：mobi 库未安装，使用备用方法")
        
        if has_mobi_lib:
            try:
                extractor = mobi.MobiExtractor(mobi_path)
                html_content = extractor.get_book_text()
                
                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text()
                    return self.clean_text(text)
                else:
                    self.log("MOBI 内容为空，使用备用方法")
            except Exception as e:
                self.log(f"MOBI 提取失败：{str(e)}，使用备用方法")
        
        # 备用方法：直接读取文件内容
        try:
            with open(mobi_path, 'rb') as f:
                data = f.read()
            encoding = self.detect_encoding(data)
            text = data.decode(encoding, errors='ignore')
            return self.clean_text(text)
        except Exception as e:
            self.log(f"备用方法失败：{str(e)}")
            raise
    
    def extract_from_txt(self, txt_path):
        with open(txt_path, 'rb') as f:
            data = f.read()
        
        encoding = self.detect_encoding(data)
        text = data.decode(encoding, errors='ignore')
        
        return self.clean_text(text)
    
    def extract_from_html(self, html_path):
        with open(html_path, 'rb') as f:
            data = f.read()
        
        encoding = self.detect_encoding(data)
        html_content = data.decode(encoding, errors='ignore')
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        return self.clean_text(text)
    
    def clean_text(self, text):
        import re
        
        # 替换多个连续空格为单个空格
        text = re.sub(r'\s{2,}', ' ', text)
        
        # 替换制表符为空格
        text = text.replace('\t', ' ')
        
        # 替换非断空格为普通空格
        text = text.replace('\xa0', ' ')
        
        # 处理行尾空格
        lines = text.splitlines()
        cleaned_lines = []
        
        for line in lines:
            # 去除行尾空格
            line = line.rstrip()
            # 保留空行以维持段落结构
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def convert_to_format(self, text_content, output_format, file_path):
        base_name = Path(file_path).stem
        
        if output_format == 'txt':
            return text_content, f"{base_name}.txt"
        
        elif output_format == 'md':
            lines = text_content.split('\n')
            md_lines = []
            
            for line in lines:
                if line.startswith('=') and len(line) > 10:
                    md_lines.append(f"# {line.strip('=').strip()}\n")
                elif line.strip():
                    md_lines.append(line)
                else:
                    md_lines.append('')
            
            md_content = '\n'.join(md_lines)
            return md_content, f"{base_name}.md"
        
        elif output_format == 'html':
            html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #444; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        h3 {{ color: #555; }}
        p {{ text-indent: 2em; margin-bottom: 1em; }}
        .metadata {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
{body}
</body>
</html>'''
            
            lines = text_content.split('\n')
            html_body = []
            
            # 识别元数据部分
            metadata_started = False
            metadata_ended = False
            metadata_lines = []
            
            for line in lines:
                if line.startswith('书名：') or line.startswith('作者：'):
                    if not metadata_started:
                        metadata_started = True
                    metadata_lines.append(line)
                elif metadata_started and line.startswith('='):
                    metadata_ended = True
                    # 添加元数据部分
                    if metadata_lines:
                        html_body.append('<div class="metadata">')
                        for meta_line in metadata_lines:
                            html_body.append(f"<p>{meta_line}</p>")
                        html_body.append('</div>')
                    # 添加标题
                    html_body.append(f"<h1>{line.strip('=').strip()}</h1>")
                elif line.startswith('=') and len(line) > 10:
                    # 根据等号数量确定标题层级
                    equals_count = len(line) - len(line.lstrip('='))
                    if equals_count >= 10:
                        html_body.append(f"<h1>{line.strip('=').strip()}</h1>")
                    elif equals_count >= 6:
                        html_body.append(f"<h2>{line.strip('=').strip()}</h2>")
                    else:
                        html_body.append(f"<h3>{line.strip('=').strip()}</h3>")
                elif line.strip():
                    html_body.append(f"<p>{line}</p>")
                else:
                    html_body.append("<br>")
            
            html_content = html_template.format(
                title=base_name,
                body='\n'.join(html_body)
            )
            return html_content, f"{base_name}.html"
        
        return text_content, f"{base_name}.txt"
    
    def convert_single_file(self, file_path, output_dir, output_format):
        try:
            text_content = self.extract_text_from_file(file_path)
            
            formatted_content, filename = self.convert_to_format(text_content, output_format, file_path)
            
            output_path = os.path.join(output_dir, filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            
            gc.collect()
            
            return True, f"成功转换：{filename}"
            
        except FileNotFoundError:
            return False, f"转换失败 {os.path.basename(file_path)}：文件不存在"
        except PermissionError:
            return False, f"转换失败 {os.path.basename(file_path)}：权限不足"
        except UnicodeDecodeError:
            return False, f"转换失败 {os.path.basename(file_path)}：编码解码错误"
        except Exception as e:
            return False, f"转换失败 {os.path.basename(file_path)}：{str(e)}"
    
    def start_conversion(self):
        if not self.files:
            messagebox.showwarning("警告", "请先添加文件")
            return
        
        output_dir = self.output_var.get()
        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return
        
        # 检查输出目录是否可写
        try:
            test_file = os.path.join(output_dir, "test_write.txt")
            with open(test_file, 'w') as f:
                f.write("")
            os.remove(test_file)
        except Exception as e:
            messagebox.showerror("错误", f"输出目录不可写：{str(e)}")
            return
        
        # 检查输入文件是否可访问
        for file_path in self.files:
            if not os.path.exists(file_path):
                messagebox.showerror("错误", f"文件不存在：{file_path}")
                return
            if not os.path.isfile(file_path):
                messagebox.showerror("错误", f"不是有效的文件：{file_path}")
                return
            if not os.access(file_path, os.R_OK):
                messagebox.showerror("错误", f"文件不可读：{file_path}")
                return
        
        if self.converting:
            return
        
        self.converting = True
        threading.Thread(target=self.convert_files, daemon=True).start()
    
    def convert_files(self):
        output_dir = self.output_var.get()
        output_format = self.output_format.get()
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.convert_button.config(state=tk.DISABLED)
        self.status_label.config(text="转换中...")
        
        total_files = len(self.files)
        self.progress['maximum'] = total_files
        self.progress['value'] = 0
        
        success_count = 0
        
        for i, file_path in enumerate(self.files):
            self.log(f"正在转换：{os.path.basename(file_path)}")
            
            success, message = self.convert_single_file(file_path, output_dir, output_format)
            self.log(message)
            
            if success:
                success_count += 1
            
            self.progress['value'] = i + 1
            self.progress_label.config(text=f"{i + 1}/{total_files}")
            self.root.update_idletasks()
        
        self.log(f"转换完成！成功：{success_count}/{total_files}")
        
        self.progress['value'] = 0
        self.progress_label.config(text="0/0")
        self.status_label.config(text="完成")
        
        self.convert_button.config(state=tk.NORMAL)
        self.converting = False
        
        messagebox.showinfo("完成", f"转换完成！\n成功转换：{success_count}/{total_files} 个文件")


def main():
    if DND_SUPPORTED:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = EbookConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
