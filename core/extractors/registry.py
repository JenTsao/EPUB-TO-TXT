#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""提取器注册表：扩展名 → 提取器实例。"""

from pathlib import Path

from core.extractors.base import BaseExtractor, UnsupportedFormatError
from core.extractors.docx_extractor import DocxExtractor
from core.extractors.epub_extractor import EpubExtractor
from core.extractors.html_extractor import HtmlExtractor
from core.extractors.mobi_extractor import MobiExtractor
from core.extractors.pdf_extractor import PdfExtractor
from core.extractors.txt_extractor import TxtExtractor

_registry: dict[str, BaseExtractor] = {
    ".epub": EpubExtractor(),
    ".mobi": MobiExtractor(),
    ".azw3": MobiExtractor(),
    ".txt": TxtExtractor(),
    ".html": HtmlExtractor(),
    ".htm": HtmlExtractor(),
    ".pdf": PdfExtractor(),
    ".docx": DocxExtractor(),
}

SUPPORTED_INPUT_FORMATS = sorted(_registry.keys())

# UI 文件选择对话框过滤器
INPUT_FILE_FILTER = (
    "电子书文件 (*.epub *.mobi *.azw3 *.txt *.html *.htm *.pdf *.docx);;"
    "EPUB (*.epub);;MOBI/AZW3 (*.mobi *.azw3);;PDF (*.pdf);;DOCX (*.docx);;"
    "文本/网页 (*.txt *.html *.htm);;所有文件 (*.*)"
)

SUPPORTED_OUTPUT_FORMATS = ["txt", "md", "html", "epub"]


def get_extractor(path: str) -> BaseExtractor:
    ext = Path(path).suffix.lower()
    extractor = _registry.get(ext)
    if extractor is None:
        raise UnsupportedFormatError(f"不支持的格式：{ext}")
    return extractor
