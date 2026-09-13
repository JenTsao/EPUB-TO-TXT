#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MOBI / AZW3 提取器（mobi 包 KindleUnpack 内核，不支持 KFX 格式）。"""

import shutil

from core.extractors.base import BaseExtractor, ConversionError, TaskControl
from core.models import BookMetadata, Chapter, ExtractionResult
from core.text import clean_text, detect_encoding

BS4_PARSER = "lxml"


class MobiExtractor(BaseExtractor):
    def _read_main_html(self, path: str) -> str:
        try:
            import mobi
        except ImportError as e:
            raise ConversionError("未安装 mobi 库，无法处理 MOBI/AZW3 文件（pip install mobi）") from e
        try:
            tempdir, filepath = mobi.extract(path)
        except Exception as e:
            raise ConversionError(f"MOBI/AZW3 解析错误：{e}") from e
        try:
            data = open(filepath, "rb").read()
            encoding = detect_encoding(data)
            return data.decode(encoding, errors="ignore")
        finally:
            shutil.rmtree(tempdir, ignore_errors=True)

    def _soup(self, html: str):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, BS4_PARSER)
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup

    def metadata(self, path: str) -> BookMetadata:
        meta = BookMetadata.from_path(path)
        try:
            soup = self._soup(self._read_main_html(path))
            if soup.title and soup.title.get_text(strip=True):
                meta.title = soup.title.get_text(strip=True)
        except Exception:
            pass
        return meta

    def extract(self, path: str, control: TaskControl | None = None) -> ExtractionResult:
        control = control or TaskControl()
        meta = BookMetadata.from_path(path)
        soup = self._soup(self._read_main_html(path))

        title = None
        if soup.title and soup.title.get_text(strip=True):
            title = soup.title.get_text(strip=True)
        else:
            for tag in soup.find_all(["h1", "h2"]):
                text = tag.get_text(strip=True)
                if text:
                    title = text
                    break
        if title and not meta.title:
            meta.title = title

        text = clean_text(soup.get_text())
        if not text.strip():
            raise ConversionError("MOBI/AZW3 文件内部没有有效文本内容")
        return ExtractionResult(metadata=meta, chapters=[Chapter(title=title, text=text)])
