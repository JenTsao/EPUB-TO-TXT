#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PDF 提取器（pypdf）：逐页提取，检测加密与无文本层（扫描版）情况。"""

from core.extractors.base import (
    BaseExtractor,
    ConversionError,
    EncryptedFileError,
    NoTextLayerError,
    TaskControl,
)
from core.models import BookMetadata, Chapter, ExtractionResult
from core.text import clean_text


def _open_reader(path: str):
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ConversionError("未安装 pypdf 库，无法处理 PDF 文件（pip install pypdf）") from e
    try:
        reader = PdfReader(path)
    except Exception as e:
        raise ConversionError(f"PDF 打开失败：{e}") from e
    if reader.is_encrypted:
        try:
            # 空密码可解开仅设置 owner 密码（限制权限）的 PDF
            if not reader.decrypt(""):
                raise EncryptedFileError("PDF 已加密，需要密码才能打开")
        except EncryptedFileError:
            raise
        except Exception as e:
            raise EncryptedFileError(f"PDF 已加密，无法自动解密：{e}") from e
    return reader


class PdfExtractor(BaseExtractor):
    def metadata(self, path: str) -> BookMetadata:
        meta = BookMetadata.from_path(path)
        try:
            reader = _open_reader(path)
            info = reader.metadata
            if info is not None:
                meta.title = info.title or None
                meta.author = info.author or None
            meta.chapter_count = len(reader.pages)
        except ConversionError:
            raise
        except Exception:
            pass
        return meta

    def extract(self, path: str, control: TaskControl | None = None) -> ExtractionResult:
        control = control or TaskControl()
        meta = BookMetadata.from_path(path)
        reader = _open_reader(path)

        info = reader.metadata
        if info is not None:
            meta.title = info.title or None
            meta.author = info.author or None

        total_pages = len(reader.pages)
        parts: list[str] = []
        for index, page in enumerate(reader.pages):
            control.pause_point()
            control.progress(index / (total_pages or 1))
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue  # 单页损坏跳过
        control.progress(1.0)

        text = clean_text("\n".join(parts))
        if not text.strip():
            raise NoTextLayerError("PDF 中未检测到文本层（可能是扫描版，需要 OCR）")
        meta.chapter_count = total_pages
        return ExtractionResult(metadata=meta, chapters=[Chapter(title=meta.title, text=text)])
