#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 单文件提取器。"""

from core.extractors.base import BaseExtractor, ConversionError, TaskControl
from core.models import BookMetadata, Chapter, ExtractionResult
from core.text import clean_text, detect_encoding

BS4_PARSER = "lxml"


def _soup(html: str):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, BS4_PARSER)
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup


class HtmlExtractor(BaseExtractor):
    def metadata(self, path: str) -> BookMetadata:
        meta = BookMetadata.from_path(path)
        try:
            data = open(path, "rb").read()
            soup = _soup(data.decode(detect_encoding(data), errors="ignore"))
            if soup.title and soup.title.get_text(strip=True):
                meta.title = soup.title.get_text(strip=True)
        except Exception:
            pass
        return meta

    def extract(self, path: str, control: TaskControl | None = None) -> ExtractionResult:
        control = control or TaskControl()
        meta = BookMetadata.from_path(path)
        try:
            data = open(path, "rb").read()
            html = data.decode(detect_encoding(data), errors="ignore")
        except OSError as e:
            raise ConversionError(f"HTML 读取失败：{e}") from e

        soup = _soup(html)
        title = None
        for tag in soup.find_all(["h1", "h2"]):
            text = tag.get_text(strip=True)
            if text:
                title = text
                break
        if not title and soup.title and soup.title.get_text(strip=True):
            title = soup.title.get_text(strip=True)
        if title and not meta.title:
            meta.title = title

        text = clean_text(soup.get_text())
        return ExtractionResult(metadata=meta, chapters=[Chapter(title=title, text=text)])
