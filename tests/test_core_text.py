"""core.text 纯函数测试（自旧版 TestCleanText / TestDetectEncoding 迁移）。"""

from unittest.mock import patch

from core.text import clean_text, detect_encoding


class TestCleanText:
    def test_collapses_spaces_and_tabs(self):
        assert clean_text("a  b\t\tc") == "a b c"

    def test_preserves_newlines(self):
        assert clean_text("line1\nline2\nline3") == "line1\nline2\nline3"

    def test_strips_trailing_whitespace(self):
        assert clean_text("hello  \nworld  ") == "hello\nworld"

    def test_collapses_multiple_blank_lines(self):
        text = "a\n\n\n\nb"
        result = clean_text(text)
        assert "\n\n\n" not in result
        assert "a" in result and "b" in result

    def test_nbsp_replaced(self):
        assert clean_text("a\xa0b") == "a b"

    def test_empty_string(self):
        assert clean_text("") == ""


class TestDetectEncoding:
    def test_returns_chardet_result(self):
        data = "你好世界".encode("utf-8")
        with patch("chardet.detect", return_value={"encoding": "utf-8", "confidence": 0.99}):
            assert detect_encoding(data) == "utf-8"

    def test_gb2312_mapped_to_gb18030(self):
        with patch("chardet.detect", return_value={"encoding": "gb2312", "confidence": 0.9}):
            assert detect_encoding(b"\xc4\xe3\xba\xc3") == "gb18030"

    def test_gbk_mapped_to_gb18030(self):
        with patch("chardet.detect", return_value={"encoding": "gbk", "confidence": 0.9}):
            assert detect_encoding(b"\xc4\xe3\xba\xc3") == "gb18030"

    def test_ascii_mapped_to_utf8(self):
        with patch("chardet.detect", return_value={"encoding": "ascii", "confidence": 1.0}):
            assert detect_encoding(b"hello") == "utf-8"

    def test_iso8859_1_not_mapped(self):
        with patch("chardet.detect", return_value={"encoding": "iso-8859-1", "confidence": 0.7}):
            assert detect_encoding(b"\xe9\xe8\xea") == "iso-8859-1"

    def test_none_encoding_defaults_utf8(self):
        with patch("chardet.detect", return_value={"encoding": None, "confidence": 0}):
            assert detect_encoding(b"hello") == "utf-8"

    def test_chardet_import_error(self):
        with patch.dict("sys.modules", {"chardet": None}):
            assert detect_encoding(b"test") == "utf-8"
