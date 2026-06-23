import re
import sys
import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from epub_to_txt_converter import EbookConverter, SUPPORTED_INPUT_FORMATS


@pytest.fixture
def converter(tmp_path):
    sys.modules["tkinter.messagebox"]._last = None
    sys.modules["tkinter.messagebox"]._last_args = None

    root = MagicMock()
    root.winfo_width.return_value = 900
    root.winfo_height.return_value = 650
    root.after.side_effect = lambda ms, fn, *a: fn(*a) if ms == 0 else None

    with patch("epub_to_txt_converter.Path.home", return_value=tmp_path):
        c = EbookConverter(root)
    c.files = []
    return c


@pytest.fixture
def msgbox():
    mb = sys.modules["tkinter.messagebox"]
    mb._last = None
    mb._last_args = None
    return mb


class TestCleanText:
    def test_collapses_spaces_and_tabs(self, converter):
        assert converter.clean_text("a  b\t\tc") == "a b c"

    def test_preserves_newlines(self, converter):
        assert converter.clean_text("line1\nline2\nline3") == "line1\nline2\nline3"

    def test_strips_trailing_whitespace(self, converter):
        assert converter.clean_text("hello  \nworld  ") == "hello\nworld"

    def test_collapses_multiple_blank_lines(self, converter):
        text = "a\n\n\n\nb"
        result = converter.clean_text(text)
        assert "\n\n\n" not in result
        assert "a" in result and "b" in result

    def test_nbsp_replaced(self, converter):
        assert converter.clean_text("a\xa0b") == "a b"

    def test_empty_string(self, converter):
        assert converter.clean_text("") == ""


class TestDetectEncoding:
    def test_returns_chardet_result(self, converter):
        data = "你好世界".encode("utf-8")
        with patch("chardet.detect", return_value={"encoding": "utf-8", "confidence": 0.99}):
            assert converter.detect_encoding(data) == "utf-8"

    def test_gb2312_mapped_to_gb18030(self, converter):
        data = b"\xc4\xe3\xba\xc3"
        with patch("chardet.detect", return_value={"encoding": "gb2312", "confidence": 0.9}):
            assert converter.detect_encoding(data) == "gb18030"

    def test_gbk_mapped_to_gb18030(self, converter):
        data = b"\xc4\xe3\xba\xc3"
        with patch("chardet.detect", return_value={"encoding": "gbk", "confidence": 0.9}):
            assert converter.detect_encoding(data) == "gb18030"

    def test_ascii_mapped_to_utf8(self, converter):
        data = b"hello"
        with patch("chardet.detect", return_value={"encoding": "ascii", "confidence": 1.0}):
            assert converter.detect_encoding(data) == "utf-8"

    def test_iso8859_1_not_mapped(self, converter):
        data = b"\xe9\xe8\xea"
        with patch("chardet.detect", return_value={"encoding": "iso-8859-1", "confidence": 0.7}):
            assert converter.detect_encoding(data) == "iso-8859-1"

    def test_none_encoding_defaults_utf8(self, converter):
        data = b"hello"
        with patch("chardet.detect", return_value={"encoding": None, "confidence": 0}):
            assert converter.detect_encoding(data) == "utf-8"

    def test_chardet_import_error(self, converter):
        with patch.dict("sys.modules", {"chardet": None}):
            assert converter.detect_encoding(b"test") == "utf-8"


class TestAddSingleFile:
    def test_adds_new_file(self, converter, tmp_path):
        f = tmp_path / "test.epub"
        f.write_text("dummy")
        assert converter.add_single_file(str(f)) is True
        assert len(converter.files) == 1

    def test_rejects_duplicate(self, converter, tmp_path):
        f = tmp_path / "test.epub"
        f.write_text("dummy")
        converter.add_single_file(str(f))
        assert converter.add_single_file(str(f)) is False
        assert len(converter.files) == 1

    def test_path_resolve_dedup(self, converter, tmp_path):
        f = tmp_path / "Test.EPUB"
        f.write_text("dummy")
        upper = tmp_path / "TEST.EPUB"
        converter.add_single_file(str(f))
        assert converter.add_single_file(str(upper)) is False

    def test_different_paths_not_deduped(self, converter, tmp_path):
        f1 = tmp_path / "a" / "test.epub"
        f2 = tmp_path / "b" / "test.epub"
        f1.parent.mkdir()
        f2.parent.mkdir()
        f1.write_text("dummy")
        f2.write_text("dummy")
        converter.add_single_file(str(f1))
        converter.add_single_file(str(f2))
        assert len(converter.files) == 2


class TestExtractFromTxt:
    def test_utf8_file(self, converter, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("你好世界\n第二行", encoding="utf-8")
        result = converter.extract_from_txt(str(f))
        assert "你好世界" in result
        assert "第二行" in result

    def test_empty_file(self, converter, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        result = converter.extract_from_txt(str(f))
        assert result == ""

    def test_binary_file_graceful(self, converter, tmp_path):
        f = tmp_path / "binary.txt"
        f.write_bytes(bytes(range(256)))
        result = converter.extract_from_txt(str(f))
        assert isinstance(result, str)


class TestExtractFromHtml:
    def test_strips_scripts_and_styles(self, converter, tmp_path):
        f = tmp_path / "test.html"
        f.write_text(
            "<html><body><h1>Title</h1>"
            "<script>alert('x')</script>"
            "<style>.x{color:red}</style>"
            "<p>Hello</p></body></html>",
            encoding="utf-8",
        )
        result = converter.extract_from_html(str(f))
        assert "Title" in result
        assert "Hello" in result
        assert "alert" not in result
        assert ".x{color:red}" not in result


class TestConvertToFormat:
    def test_txt_passthrough(self, converter):
        content, name = converter.convert_to_format("hello", "txt", "/a/book.epub")
        assert content == "hello"
        assert name == "book.txt"

    def test_md_with_equals_title(self, converter):
        content, name = converter.convert_to_format("==== Title\n\nbody", "md", "/a/book.epub")
        assert "# Title" in content
        assert "body" in content
        assert name == "book.md"

    def test_md_with_separator(self, converter):
        content, _ = converter.convert_to_format("line1\n---\nline2", "md", "/a/b.epub")
        assert "---\n" in content

    def test_html_structure(self, converter):
        content, name = converter.convert_to_format("Hello World", "html", "/a/book.epub")
        assert "<!DOCTYPE html>" in content
        assert "Hello World" in content
        assert name == "book.html"

    def test_html_metadata_with_title_author(self, converter):
        text = "书名：测试书\n作者：作者A\n---\n正文内容"
        content, _ = converter.convert_to_format(text, "html", "/a/b.epub")
        assert "metadata" in content
        assert "测试书" in content
        assert "作者A" in content

    def test_html_metadata_without_title(self, converter):
        text = "---\n正文内容"
        content, _ = converter.convert_to_format(text, "html", "/a/b.epub")
        assert "<hr>" in content
        assert "正文内容" in content

    def test_html_heading_levels(self, converter):
        text = "========== Big\n\n====== Medium\n\n=== Small"
        content, _ = converter.convert_to_format(text, "html", "/a/b.epub")
        assert "<h1>" in content
        assert "<h2>" in content
        assert "<h3>" in content

    def test_html_empty_title_ignored(self, converter):
        text = "=====\n\n正文"
        content, _ = converter.convert_to_format(text, "html", "/a/b.epub")
        assert "<h1>" not in content


class TestExtractFromEpub:
    def _make_epub(self, tmp_path, title="Test Book", author="Author", body="<p>Hello</p>"):
        from ebooklib import epub

        book = epub.EpubBook()
        book.set_identifier("test-001")
        book.set_title(title)
        book.set_language("zh")
        book.add_author(author)

        c1 = epub.EpubHtml(title="Ch1", file_name="ch1.xhtml", lang="zh")
        c1.set_content(body)
        book.add_item(c1)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", c1]

        epub_path = tmp_path / "test.epub"
        epub.write_epub(str(epub_path), book)
        return epub_path

    def test_extracts_title_and_author(self, converter, tmp_path):
        epub_path = self._make_epub(tmp_path, title="测试书", author="张三")
        result = converter.extract_from_epub(str(epub_path))
        assert "书名：测试书" in result
        assert "作者：张三" in result
        assert "Hello" in result

    def test_no_metadata_no_separator(self, converter, tmp_path):
        from ebooklib import epub as epub_mod

        book = epub_mod.EpubBook()
        book.set_identifier("meta-test")
        book.set_title("")
        book.set_language("zh")
        c1 = epub_mod.EpubHtml(title="Ch1", file_name="ch1.xhtml", lang="zh")
        c1.set_content("<p>Content</p>")
        book.add_item(c1)
        book.add_item(epub_mod.EpubNcx())
        book.add_item(epub_mod.EpubNav())
        book.spine = ["nav", c1]
        epub_path = tmp_path / "no_meta.epub"
        epub_mod.write_epub(str(epub_path), book)

        result = converter.extract_from_epub(str(epub_path))
        assert "Content" in result

    def test_strips_svg(self, converter, tmp_path):
        epub_path = self._make_epub(tmp_path, body="<p>Text</p><svg><circle/></svg><p>End</p>")
        result = converter.extract_from_epub(str(epub_path))
        assert "Text" in result
        assert "End" in result


class TestExtractFromMobi:
    def test_calls_mobi_extract(self, converter, tmp_path):
        mobi_tmp = tmp_path / "tmp"
        mobi_tmp.mkdir()
        html_file = mobi_tmp / "book.html"
        html_file.write_text("<html><body><p>MOBI text</p></body></html>")

        fake_mobi = types.ModuleType("mobi")
        fake_mobi.extract = MagicMock(return_value=(str(mobi_tmp), str(html_file)))

        fake_bs4 = types.ModuleType("bs4")
        from bs4 import BeautifulSoup
        fake_bs4.BeautifulSoup = BeautifulSoup

        with patch.dict("sys.modules", {"mobi": fake_mobi, "bs4": fake_bs4}):
            with patch("epub_to_txt_converter.HAS_MOBI", True):
                result = converter.extract_from_mobi("dummy.mobi")
                assert isinstance(result, str)
                assert "MOBI text" in result
                fake_mobi.extract.assert_called_once_with("dummy.mobi")


class TestStartConversion:
    def test_blocks_when_no_files(self, converter, msgbox):
        converter.files = []
        converter.start_conversion()
        assert msgbox._last is not None

    def test_blocks_when_converting(self, converter, msgbox):
        converter.files = ["/dummy.epub"]
        converter.converting = True
        converter.start_conversion()
        converter.converting = False

    def test_blocks_when_no_output_dir(self, converter, msgbox):
        converter.files = ["/dummy.epub"]
        converter.converting = False
        converter.output_var = MagicMock()
        converter.output_var.get.return_value = ""
        converter.start_conversion()
        assert msgbox._last is not None
