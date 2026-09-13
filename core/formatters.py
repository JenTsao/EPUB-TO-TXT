#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""输出格式化器：将 ExtractionResult 的结构化章节渲染为 txt / md / html / epub。"""

import html as html_module
from pathlib import Path

from core.extractors.base import UnsupportedFormatError
from core.models import ExtractionResult

OUTPUT_EXTENSIONS = {"txt": ".txt", "md": ".md", "html": ".html", "epub": ".epub"}


def output_filename(source_path: str, output_format: str) -> str:
    base_name = Path(source_path).stem
    return base_name + OUTPUT_EXTENSIONS.get(output_format, ".txt")


def _has_metadata(result: ExtractionResult) -> bool:
    meta = result.metadata
    return bool(meta.title or meta.author)


def format_txt(result: ExtractionResult) -> str:
    lines: list[str] = []
    meta = result.metadata
    if meta.title:
        lines.append(f"书名：{meta.title}")
    if meta.author:
        lines.append(f"作者：{meta.author}")
    if _has_metadata(result):
        lines.extend(["---", ""])
    for index, chapter in enumerate(result.chapters):
        if chapter.title:
            lines.append(chapter.title)
        lines.append(chapter.text)
        if index < len(result.chapters) - 1:
            lines.append("")
    return "\n".join(lines)


def format_md(result: ExtractionResult) -> str:
    lines: list[str] = []
    meta = result.metadata
    if meta.title:
        lines.append(f"# {meta.title}")
    if meta.author:
        lines.append(f"作者：{meta.author}")
    if _has_metadata(result):
        lines.extend(["---", ""])
    for chapter in result.chapters:
        if chapter.title:
            lines.extend([f"## {chapter.title}", ""])
        if chapter.text:
            lines.extend([chapter.text, ""])
    return "\n".join(lines).rstrip("\n") + "\n"


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{ font-family: "Microsoft YaHei", Arial, sans-serif; margin: 40px auto; line-height: 1.6; max-width: 800px; padding: 0 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #444; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        p {{ text-indent: 2em; margin-bottom: 1em; }}
        .metadata {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; text-indent: 0; }}
        .metadata p {{ text-indent: 0; margin: 5px 0; }}
    </style>
</head>
<body>
{body}
</body>
</html>"""


def format_html(result: ExtractionResult, source_path: str) -> str:
    body: list[str] = []
    meta = result.metadata

    if _has_metadata(result):
        body.append('<div class="metadata">')
        if meta.title:
            body.append(f"<p>书名：{html_module.escape(meta.title)}</p>")
        if meta.author:
            body.append(f"<p>作者：{html_module.escape(meta.author)}</p>")
        body.append("</div>")

    for chapter in result.chapters:
        if chapter.title:
            body.append(f"<h2>{html_module.escape(chapter.title)}</h2>")
        for line in chapter.text.splitlines():
            if line.strip():
                body.append(f"<p>{html_module.escape(line)}</p>")

    title = meta.title or Path(source_path).stem
    return _HTML_TEMPLATE.format(title=html_module.escape(title), body="\n".join(body))


def format_epub(result: ExtractionResult, source_path: str) -> bytes:
    """用 ebooklib 生成 EPUB（按章节建 EpubHtml）。"""
    from ebooklib import epub

    meta = result.metadata
    book = epub.EpubBook()
    base_name = Path(source_path).stem
    book.set_identifier(f"converted-{base_name}")
    book.set_title(meta.title or base_name)
    book.set_language("zh")
    if meta.author:
        book.add_author(meta.author)

    spine_items = ["nav"]
    for index, chapter in enumerate(result.chapters, start=1):
        item = epub.EpubHtml(title=chapter.title or f"第{index}章", file_name=f"ch{index:04d}.xhtml", lang="zh")
        paragraphs = "".join(
            f"<p>{html_module.escape(line)}</p>" for line in chapter.text.splitlines() if line.strip()
        )
        heading = f"<h2>{html_module.escape(chapter.title)}</h2>" if chapter.title else ""
        item.set_content(f"<html><body>{heading}{paragraphs}</body></html>")
        book.add_item(item)
        spine_items.append(item)

    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine_items

    import io

    buffer = io.BytesIO()
    epub.write_epub(buffer, book)
    return buffer.getvalue()


def format_result(result: ExtractionResult, output_format: str, source_path: str) -> tuple[str | bytes, str]:
    """返回 (内容, 输出文件名)。epub 返回 bytes，其余返回 str。"""
    if output_format == "txt":
        return format_txt(result), output_filename(source_path, "txt")
    if output_format == "md":
        return format_md(result), output_filename(source_path, "md")
    if output_format == "html":
        return format_html(result, source_path), output_filename(source_path, "html")
    if output_format == "epub":
        return format_epub(result, source_path), output_filename(source_path, "epub")
    raise UnsupportedFormatError(f"不支持的输出格式：{output_format}")
