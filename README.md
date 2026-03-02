# EPUB 转 TXT 工具

一个简单易用的 EPUB 电子书转 TXT 文本文件的工具，带有图形用户界面。

## 功能特点

- 🖥️ 友好的图形用户界面
- 📚 支持批量转换多个 EPUB 文件
- 📁 支持添加整个文件夹中的 EPUB 文件
- 📝 自动提取书名、作者等元信息
- 🧹 智能清理 HTML 标签和格式
- 📊 实时显示转换进度
- 📋 详细的转换日志

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

1. 运行程序：
   ```bash
   python epub_to_txt_converter.py
   ```

2. 使用界面：
   - **添加文件**: 选择单个或多个 EPUB 文件
   - **添加文件夹**: 选择包含 EPUB 文件的文件夹，自动添加所有 EPUB 文件
   - **选择输出目录**: 设置转换后的 TXT 文件保存位置
   - **开始转换**: 点击开始批量转换

3. 转换完成后，TXT 文件将保存在指定的输出目录中

## 输出格式

转换后的 TXT 文件包含：
- 书名和作者信息（如果有）
- 清理后的正文内容
- 保持基本的段落结构

## 注意事项

- 确保 EPUB 文件没有 DRM 保护
- 转换过程中请不要关闭程序
- 大文件转换可能需要一些时间
- 输出的 TXT 文件采用 UTF-8 编码

## 故障排除

如果遇到问题：
1. 检查 EPUB 文件是否损坏
2. 确保有足够的磁盘空间
3. 检查输出目录的写入权限
4. 查看转换日志了解具体错误信息

## 依赖包说明

- `ebooklib`: 用于读取和解析 EPUB 文件
- `beautifulsoup4`: 用于解析 HTML 内容
- `lxml`: BeautifulSoup 的 XML 解析器
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
