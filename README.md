# 电子书转换工具 v3.0

[![CI](https://github.com/jencaoking/EPUB-TO-TXT/actions/workflows/ci.yml/badge.svg)](https://github.com/jencaoking/EPUB-TO-TXT/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

一个简单易用的电子书转换工具，支持 EPUB / MOBI / AZW3 / PDF / DOCX 等格式批量转换为 TXT / Markdown / HTML / EPUB，基于 PySide6（Qt）构建现代化图形界面。

## 功能特点

- 🖥️ **PySide6 界面** - 全新 Qt 界面，支持深色/浅色主题切换
- 📚 **多格式输入** - 支持 EPUB、MOBI、AZW3、PDF、DOCX、TXT、HTML
- 📝 **多格式输出** - 支持输出为 TXT、Markdown、HTML、EPUB（按章节结构生成）
- 🚀 **并发转换** - 线程池并行处理批量任务，支持暂停 / 继续 / 取消
- 🔍 **元信息预览** - 添加文件后自动显示书名、作者、章节数；转换完成后回填字数
- ✨ **原生拖拽** - 直接拖拽文件或文件夹到窗口
- 🧹 **智能文本清洗** - 自动检测编码、清理 HTML 标签、合并多余空行
- ⚙️ **设置持久化** - 自动记住输出目录、输出格式、窗口大小、主题
- 📂 **重名保护** - 不同目录同名文件转换时自动追加序号，不会互相覆盖
- 📋 **实时日志** - 详细的转换日志与进度显示

## 支持格式

### 输入格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| EPUB | .epub | 主流电子书格式，按 spine 顺序提取章节 |
| MOBI | .mobi | Amazon Kindle 格式 |
| AZW3 | .azw3 | Kindle KF8 格式（不支持 KFX） |
| PDF | .pdf | 逐页提取文本，自动检测加密与扫描版 |
| DOCX | .docx | 按 Heading 样式自动切分章节 |
| TXT | .txt | 纯文本文件 |
| HTML | .html / .htm | 网页文件 |

### 输出格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| TXT | .txt | 纯文本（默认），保留书名、作者与章节标题 |
| Markdown | .md | 书名/章节自动转为标题层级 |
| HTML | .html | 带样式的网页，支持浏览器直接打开 |
| EPUB | .epub | 按章节生成完整电子书 |

## 快速开始

### 环境要求

- Python 3.10+
- 依赖包见 [requirements.txt](requirements.txt)

### 安装运行

```bash
pip install -r requirements.txt
python main.py
```

Windows 用户也可以直接双击 `run.bat`（自动检测并安装依赖）。

### 使用打包版

无需安装 Python，直接运行仓库中的 `电子书转换工具.exe`，或从 [Releases](https://github.com/jencaoking/EPUB-TO-TXT/releases) 下载最新版本。

### 使用步骤

1. 添加文件：点击「添加文件 / 添加文件夹」，或直接拖拽到窗口
2. 选择输出格式（TXT / MD / HTML / EPUB）
3. 设置输出目录
4. 点击「开始转换」；转换中可随时暂停 / 继续 / 取消
5. 转换完成后可直接打开输出目录

## 项目结构

```
EPUB TO TXT/
├── main.py                      # 程序入口
├── core/                        # 转换核心（纯 Python，无 GUI 依赖）
│   ├── engine.py                # 并发引擎：线程池调度、暂停/取消
│   ├── extractors/              # 各格式提取器（epub/mobi/pdf/docx/txt/html）
│   ├── formatters.py            # 输出格式化器（txt/md/html/epub）
│   ├── models.py                # 数据模型（章节、元信息）
│   └── text.py                  # 文本清洗与编码检测
├── ui/                          # PySide6 界面层
│   ├── main_window.py           # 主窗口
│   ├── file_table_model.py      # 文件列表表格模型
│   ├── engine_bridge.py         # 引擎回调 → Qt 信号桥
│   ├── metadata_worker.py       # 元信息后台加载
│   └── settings.py              # QSettings 持久化 + 主题管理
├── tests/                       # pytest 测试（含引擎并发与 UI 冒烟测试）
├── build_exe.py                 # PyInstaller 打包脚本
└── .github/workflows/ci.yml     # CI：自动测试 + 云端打包 + Release
```

## CI / 自动化

项目通过 GitHub Actions 自动化（[ci.yml](.github/workflows/ci.yml)）：

- **自动测试** - 每次推送在 Windows / Linux × Python 3.12 / 3.13 矩阵上运行全部测试，并生成覆盖率报告
- **云端打包** - 测试通过后自动用 PyInstaller 打包 exe，可在 Actions 的 Artifacts 下载
- **自动发布** - 推送 `v*` 标签（如 `git tag v3.0.0 && git push --tags`）时自动创建 Release 并附上 exe

## 注意事项

- 确保电子书文件没有 DRM 保护
- PDF 为扫描版（无文本层）时无法提取，需要 OCR 工具配合
- 设置了打开密码的 PDF 无法转换（仅限制编辑权限的 PDF 可以）
- Kindle 新版 KFX 格式暂不支持
- 输出文件采用 UTF-8 编码

## 故障排除

如果遇到问题：
1. 查看转换日志了解具体错误信息
2. 检查电子书文件是否损坏
3. 确保有足够的磁盘空间和输出目录写入权限
4. 提交 [Issue](https://github.com/jencaoking/EPUB-TO-TXT/issues) 并附上日志

## 依赖包说明

- `PySide6`: Qt 图形用户界面
- `ebooklib`: EPUB 读取与生成
- `beautifulsoup4` + `lxml`: HTML 内容解析
- `mobi`: MOBI / AZW3 格式支持
- `pypdf`: PDF 文本提取
- `python-docx`: DOCX 读取
- `chardet`: 编码检测

## 更新日志

### v3.0 (2026-09-13)

🚀 **重大重构**：
- 界面从 tkinter 迁移到 PySide6（Qt），原生支持拖拽与深色/浅色主题
- 代码模块化拆分：`core/`（转换核心，无 GUI 依赖）+ `ui/`（界面层），核心逻辑可独立测试
- 线程池并发转换，支持暂停 / 继续 / 取消，完成后一键打开输出目录
- 新增输入格式：PDF（pypdf）、DOCX（python-docx）、AZW3
- 新增输出格式：EPUB（按章节结构生成）
- 新增文件元信息预览（书名 / 作者 / 章节数 / 字数）
- 设置持久化（QSettings）：输出目录、格式、窗口大小、主题
- 性能优化：EPUB 解析改用 lxml、多任务并行、元信息轻量读取（不解析全文）
- 修复：EPUB 章节顺序不保证（改按 spine 遍历）、不同目录同名文件互相覆盖
- 新增 GitHub Actions CI：多平台测试矩阵 + 云端打包 + 自动 Release

### v2.1 (2026-06-23)

🐛 **BUG 修复**：
- 修复打包脚本误排除 tkinter 子模块导致 exe 无法启动
- 修复 MOBI 转换调用不存在的 API
- 修复 clean_text 将换行符压成空格的问题
- 修复 requirements.txt 版本冲突（lxml>=6.0.0）
- 修复 build.bat 通配符删除 spec 文件写法
- 修复输出目录权限检测误报（先建目录再测试写入）
- 修复重复文件判断在 Linux 失效的问题
- 修复 HTML 输出的 metadata 处理漏洞
- 修复连续转换时进度条提前满格
- 统一版本号为 v2.1

### v2.0 (2026-03-02)

🚀 **重大更新**：
- 新增拖拽支持，可以直接拖拽文件/文件夹到窗口
- 新增多格式输入支持（EPUB、MOBI、TXT、HTML）
- 新增多格式输出支持（TXT、Markdown、HTML）
- 性能优化，降低内存占用
- 智能编码检测，解决乱码问题

### v1.1 (2026-03-02)

- 🐛 修复：输出目录设置逻辑，桌面不存在时自动回退到用户主目录
- 🐛 修复：文件重复检查逻辑，使用绝对路径比较避免重复添加
- 🐛 修复：错误处理机制，日志中记录详细错误信息
- 🐛 修复：进度条重置问题，转换完成后自动重置
- ✨ 改进：增强用户体验和程序稳定性

### v1.0.0 (2025-10-26)

- 首次发布
- 支持 EPUB 到 TXT 的批量转换
- 图形用户界面
- 进度显示和日志记录
- 自动元信息提取
- 智能文本清理
- 采用 Apache 2.0 开源协议

## 开源协议

本项目采用 Apache 2.0 开源协议。详见 [LICENSE](LICENSE) 文件。

### 主要权限

- ✅ 商业使用
- ✅ 修改代码
- ✅ 分发
- ✅ 专利使用
- ✅ 私有使用

### 限制条件

- 需要保留原始许可证和版权声明
- 需要说明修改内容
- 不提供担保
- 商标使用权未授予

## 许可证

Copyright 2025-2026

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
