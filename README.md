# 电子书转换工具 v2.1

一个简单易用的电子书转换为 TXT/MD/HTML 格式的工具，带有图形用户界面。

## 功能特点

### 🆕 v2.1 新功能

- ✨ **拖拽支持** - 支持拖拽文件或文件夹到窗口
- 📚 **多格式支持** - 支持 EPUB、MOBI、TXT、HTML 等格式
- 📝 **多输出格式** - 支持输出为 TXT、Markdown(MD)、HTML 格式
- ⚡ **性能优化** - 降低内存占用，转换更高效
- 🔍 **智能编码检测** - 自动检测文件编码，解决乱码问题

### 基础功能

- 🖥️ 友好的图形用户界面
- 📚 支持批量转换多个电子书文件
- 📁 支持添加整个文件夹中的电子书文件
- 📝 自动提取书名、作者等元信息
- 🧹 智能清理 HTML 标签和格式
- 📊 实时显示转换进度
- 📋 详细的转换日志

## 支持格式

### 输入格式
| 格式 | 扩展名 | 说明 |
|------|--------|------|
| EPUB | .epub | 主流电子书格式 |
| MOBI | .mobi | Amazon Kindle 格式 |
| TXT | .txt | 纯文本文件 |
| HTML | .html / .htm | 网页文件 |

### 输出格式
| 格式 | 扩展名 | 说明 |
|------|--------|------|
| TXT | .txt | 纯文本（默认） |
| Markdown | .md | 带格式标记的文本 |
| HTML | .html | 网页格式 |

## 安装要求

- Python 3.6+
- 所需的 Python 包（见 requirements.txt）

## 安装步骤

1. 确保已安装 Python 3.6 或更高版本
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

### 基础使用

1. 运行程序：
   ```bash
   python epub_to_txt_converter.py
   ```

2. 添加文件：
   - 点击"添加文件"选择电子书
   - 点击"添加文件夹"批量添加
   - **直接拖拽文件或文件夹到窗口** ✨

3. 选择输出格式（TXT / Markdown / HTML）

4. 设置输出目录

5. 点击"开始转换"

### 拖拽使用（推荐）

✨ **v2.0 新功能** - 直接拖拽：
- 单个文件 → 添加到转换列表
- 文件夹 → 自动添加文件夹中所有支持的电子书
- 多个文件 → 批量添加

## 输出格式说明

### TXT 格式
- 纯文本输出
- 保留书名、作者信息
- 自动清理 HTML 标签
- 适合阅读和进一步处理

### Markdown 格式
- 保留基本格式结构
- 标题自动转换为 Markdown 标题
- 适合文档编辑和分享

### HTML 格式
- 美化的网页输出
- 自动添加样式
- 支持浏览器直接打开
- 适合发布和分享

## 注意事项

- 确保电子书文件没有 DRM 保护
- 转换过程中请不要关闭程序
- 大文件转换可能需要一些时间
- 输出的文件采用 UTF-8 编码

## 故障排除

如果遇到问题：
1. 检查电子书文件是否损坏
2. 确保有足够的磁盘空间
3. 检查输出目录的写入权限
4. 查看转换日志了解具体错误信息

## 依赖包说明

- `ebooklib`: 用于读取和解析 EPUB 文件
- `beautifulsoup4`: 用于解析 HTML 内容
- `lxml`: BeautifulSoup 的 XML 解析器
- `chardet`: 编码检测
- `mobi`: MOBI 格式支持
- `tkinter`: Python 内置的 GUI 库

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

## 更新日志

### v2.1 (2026-06-23)
🐛 **BUG 修复**:
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
🚀 **重大更新**:
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

## 许可证

Copyright 2025

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
