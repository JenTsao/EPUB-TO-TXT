#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EPUB 提取器：元信息走 zipfile+lxml 轻量路径；全文走 ebooklib 并按 spine 顺序提取章节。"""

import warnings
import zipfile

from lxml import etree

from core.extractors.base import BaseExtractor, ConversionError, TaskControl
from core.models import BookMetadata, Chapter, ExtractionResult
from core.text import clean_text

BS4_PARSER = "lxml"


def _soup(content: bytes):
    from bs4 import BeautifulSoup

    return BeautifulSoup(content, BS4_PARSER)


def _extract_first_heading(soup):
    """取第一个 h1/h2/h3 文本作为章节标题，并将其从正文中移除。"""
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text:
            tag.decompose()
            return text
    return None


class EpubExtractor(BaseExtractor):
    def metadata(self, path: str) -> BookMetadata:
        meta = BookMetadata.from_path(path)
        try:
            with zipfile.ZipFile(path) as zf:
                container = zf.read("META-INF/container.xml")
                root = etree.fromstring(container)
                rootfile = root.find(".//{*}rootfile")
                if rootfile is None:
                    return meta
                opf = etree.fromstring(zf.read(rootfile.get("full-path")))
                meta.title = opf.findtext(".//{*}title") or None
                meta.author = opf.findtext(".//{*}creator") or None
                spine_count = len(opf.findall(".//{*}spine/{*}itemref"))
                # 排除 manifest 中标记为导航页的条目
                nav_count = sum(
                    1 for it in opf.findall(".//{*}manifest/{*}item") if "nav" in (it.get("properties") or "")
                )
                meta.chapter_count = (spine_count - nav_count) or None
        except Exception:
            # 轻量读取失败不影响转换，返回基础信息即可
            pass
        return meta

    def extract(self, path: str, control: TaskControl | None = None) -> ExtractionResult:
        from ebooklib import ITEM_DOCUMENT, epub

        control = control or TaskControl()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                book = epub.read_epub(path)
        except ConversionError:
            raise
        except Exception as e:
            raise ConversionError(f"EPUB 提取失败：{e}") from e

        meta = BookMetadata.from_path(path)
        try:
            title = book.get_metadata("DC", "title")
            author = book.get_metadata("DC", "creator")
            meta.title = str(title[0][0]) if title else None
            meta.author = str(author[0][0]) if author else None
        except Exception:
            pass

        # 按 spine 顺序遍历（修复旧版 get_items() 的 manifest 序乱序问题），nav 页不算章节
        spine_ids = [entry[0] if isinstance(entry, tuple) else entry for entry in book.spine]
        documents = []
        for item_id in spine_ids:
            item = book.get_item_with_id(item_id)
            if item is not None and item.get_type() == ITEM_DOCUMENT and not isinstance(item, epub.EpubNav):
                documents.append(item)
        if not documents:
            documents = [
                item
                for item in book.get_items_of_type(ITEM_DOCUMENT)
                if not isinstance(item, epub.EpubNav)
            ]

        chapters: list[Chapter] = []
        total = len(documents) or 1
        for index, item in enumerate(documents):
            control.pause_point()
            control.progress(index / total)
            try:
                soup = _soup(item.get_content())
                for tag in soup(["script", "style", "svg"]):
                    tag.decompose()
                chapter_title = _extract_first_heading(soup)
                text = clean_text(soup.get_text())
                if text.strip():
                    chapters.append(Chapter(title=chapter_title, text=text))
            except Exception as e:
                # 单章损坏跳过，不中断整本书
                print(f"处理 EPUB 章节时跳过出错内容：{e}")
        control.progress(1.0)

        if not chapters:
            raise ConversionError("EPUB 中没有可提取的正文内容")
        return ExtractionResult(metadata=meta, chapters=chapters)
