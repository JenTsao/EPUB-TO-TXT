#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文本处理纯函数：编码检测与文本清洗（从旧版 EbookConverter 摘出，行为保持一致）。"""

import re

# chardet 常见误报编码 → 更准确的解码器
_ENCODING_MAP = {
    "gb2312": "gb18030",
    "gbk": "gb18030",
    "ascii": "utf-8",
}

_WHITESPACE_RE = re.compile(r"[ \t]{2,}")


def detect_encoding(data: bytes) -> str:
    """检测字节流的文本编码，失败时回退 utf-8。"""
    try:
        import chardet

        result = chardet.detect(data)
        encoding = result.get("encoding")
        if encoding:
            encoding = encoding.lower()
            return _ENCODING_MAP.get(encoding, encoding)
        return "utf-8"
    except ImportError:
        return "utf-8"
    except Exception:
        return "utf-8"


def clean_text(text: str) -> str:
    """清洗文本：压缩多余空白、去除制表符与 nbsp、合并连续空行。"""
    text = _WHITESPACE_RE.sub(" ", text)
    text = text.replace("\t", " ").replace("\xa0", " ")

    cleaned_lines: list[str] = []
    for line in text.splitlines():
        line = line.rstrip()
        if line or (cleaned_lines and cleaned_lines[-1]):
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines)
