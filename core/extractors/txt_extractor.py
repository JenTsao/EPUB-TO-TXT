#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""TXT 提取器：自动检测编码后整体读取。"""

from core.extractors.base import BaseExtractor, ConversionError, TaskControl
from core.models import BookMetadata, Chapter, ExtractionResult
from core.text import clean_text, detect_encoding


class TxtExtractor(BaseExtractor):
    def metadata(self, path: str) -> BookMetadata:
        return BookMetadata.from_path(path)

    def extract(self, path: str, control: TaskControl | None = None) -> ExtractionResult:
        control = control or TaskControl()
        meta = BookMetadata.from_path(path)
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            raise ConversionError(f"TXT 读取失败：{e}") from e
        text = clean_text(data.decode(detect_encoding(data), errors="ignore"))
        return ExtractionResult(metadata=meta, chapters=[Chapter(text=text)])
