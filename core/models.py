#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心数据模型：所有提取器与格式化器之间的中间表示。"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Chapter:
    """单个章节：title 为可识别的章节标题（可为 None），text 为正文文本。"""

    title: str | None = None
    text: str = ""


@dataclass
class BookMetadata:
    """书籍元信息。word_count 在转换完成后由引擎回填。"""

    path: str = ""
    fmt: str = ""
    size_bytes: int = 0
    title: str | None = None
    author: str | None = None
    chapter_count: int | None = None
    word_count: int | None = None

    @classmethod
    def from_path(cls, path: str) -> "BookMetadata":
        p = Path(path)
        return cls(path=str(p), fmt=p.suffix.lower().lstrip("."), size_bytes=p.stat().st_size)


@dataclass
class ExtractionResult:
    """提取结果：结构化章节列表，是所有输出格式（txt/md/html/epub）的共同输入。"""

    metadata: BookMetadata
    chapters: list[Chapter] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(len(ch.text) for ch in self.chapters)
