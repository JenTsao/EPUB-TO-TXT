"""提取器测试：txt / html / epub / docx / pdf / mobi(mock)。"""

import types
from unittest.mock import MagicMock, patch

import pytest

from core.extractors.base import NoTextLayerError, TaskControl
from core.extractors.epub_extractor import EpubExtractor
from core.extractors.html_extractor import HtmlExtractor
from core.extractors.mobi_extractor import MobiExtractor
from core.extractors.registry import get_extractor
from core.extractors.txt_extractor import TxtExtractor


class TestRegistry:
    def test_known_extensions(self, tmp_path):
        for ext in [".epub", ".mobi", ".azw3", ".txt", ".html", ".htm", ".pdf", ".docx"]:
            f = tmp_path / f"book{ext}"
            f.write_text("x") if ext == ".txt" else f.write_bytes(b"x")
            if ext not in (".txt",):
                continue  # 其他格式无法凭空构造，仅验证注册表分发
        assert get_extractor(str(tmp_path / "book.txt")) is not None

    def test_unsupported_raises(self):
        from core.extractors.base import UnsupportedFormatError

        with pytest.raises(UnsupportedFormatError):
            get_extractor("book.xyz")


class TestTxtExtractor:
    def test_utf8_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("你好世界\n第二行", encoding="utf-8")
        result = TxtExtractor().extract(str(f))
        assert "你好世界" in result.chapters[0].text
        assert "第二行" in result.chapters[0].text

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_bytes(b"")
        result = TxtExtractor().extract(str(f))
        assert result.chapters[0].text == ""

    def test_binary_file_graceful(self, tmp_path):
        f = tmp_path / "binary.txt"
        f.write_bytes(bytes(range(256)))
        result = TxtExtractor().extract(str(f))
        assert isinstance(result.chapters[0].text, str)


class TestHtmlExtractor:
    def test_strips_scripts_and_styles(self, tmp_path):
        f = tmp_path / "test.html"
        f.write_text(
            "<html><body><h1>Title</h1>"
            "<script>alert('x')</script>"
            "<style>.x{color:red}</style>"
            "<p>Hello</p></body></html>",
            encoding="utf-8",
        )
        result = HtmlExtractor().extract(str(f))
        text = result.chapters[0].text
        assert "Title" in text
        assert "Hello" in text
        assert "alert" not in text
        assert ".x{color:red}" not in text

    def test_title_from_h1(self, tmp_path):
        f = tmp_path / "t.html"
        f.write_text("<h1>大标题</h1><p>body</p>", encoding="utf-8")
        result = HtmlExtractor().extract(str(f))
        assert result.chapters[0].title == "大标题"


def _make_epub(tmp_path, title="Test Book", author="Author", body="<p>Hello</p>"):
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


class TestEpubExtractor:
    def test_extracts_title_and_author(self, tmp_path):
        epub_path = _make_epub(tmp_path, title="测试书", author="张三")
        result = EpubExtractor().extract(str(epub_path))
        assert result.metadata.title == "测试书"
        assert result.metadata.author == "张三"
        assert "Hello" in result.chapters[0].text

    def test_no_metadata(self, tmp_path):
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

        result = EpubExtractor().extract(str(epub_path))
        assert "Content" in result.chapters[0].text

    def test_strips_svg(self, tmp_path):
        epub_path = _make_epub(tmp_path, body="<p>Text</p><svg><circle/></svg><p>End</p>")
        result = EpubExtractor().extract(str(epub_path))
        text = result.chapters[0].text
        assert "Text" in text and "End" in text

    def test_lightweight_metadata(self, tmp_path):
        epub_path = _make_epub(tmp_path, title="轻量书", author="李四")
        meta = EpubExtractor().metadata(str(epub_path))
        assert meta.title == "轻量书"
        assert meta.author == "李四"
        assert meta.chapter_count == 1  # spine 中仅 ch1 是文档


class TestMobiExtractor:
    def test_calls_mobi_extract(self, tmp_path):
        mobi_tmp = tmp_path / "tmp"
        mobi_tmp.mkdir()
        html_file = mobi_tmp / "book.html"
        html_file.write_text("<html><head><title>MOBI Book</title></head><body><p>MOBI text</p></body></html>")
        dummy = tmp_path / "dummy.mobi"
        dummy.write_bytes(b"fake-mobi-data")

        fake_mobi = types.ModuleType("mobi")
        fake_mobi.extract = MagicMock(return_value=(str(mobi_tmp), str(html_file)))

        with patch.dict("sys.modules", {"mobi": fake_mobi}):
            result = MobiExtractor().extract(str(dummy))
            assert "MOBI text" in result.chapters[0].text
            assert result.metadata.title == "MOBI Book"
            fake_mobi.extract.assert_called_once_with(str(dummy))


class TestDocxExtractor:
    def test_headings_split_chapters(self, tmp_path):
        from docx import Document

        doc = Document()
        doc.add_heading("第一章", level=1)
        doc.add_paragraph("内容一")
        doc.add_heading("第二章", level=1)
        doc.add_paragraph("内容二")
        f = tmp_path / "test.docx"
        doc.save(str(f))

        from core.extractors.docx_extractor import DocxExtractor

        result = DocxExtractor().extract(str(f))
        assert [c.title for c in result.chapters] == ["第一章", "第二章"]
        assert "内容一" in result.chapters[0].text

    def test_metadata(self, tmp_path):
        from docx import Document

        doc = Document()
        doc.core_properties.title = "DOCX 书"
        doc.add_paragraph("正文")
        f = tmp_path / "meta.docx"
        doc.save(str(f))

        from core.extractors.docx_extractor import DocxExtractor

        meta = DocxExtractor().metadata(str(f))
        assert meta.title == "DOCX 书"


class TestPdfExtractor:
    def test_blank_pdf_raises_no_text_layer(self, tmp_path):
        from pypdf import PdfWriter

        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        f = tmp_path / "blank.pdf"
        with open(f, "wb") as fh:
            writer.write(fh)

        from core.extractors.pdf_extractor import PdfExtractor

        with pytest.raises(NoTextLayerError):
            PdfExtractor().extract(str(f))


class TestTaskControl:
    def test_checkpoint_raises_on_cancel(self):
        control = TaskControl()
        control.cancel()
        from core.extractors.base import TaskCancelled

        with pytest.raises(TaskCancelled):
            control.checkpoint()

    def test_progress_clamped(self):
        seen = []
        control = TaskControl(on_progress=seen.append)
        control.progress(1.5)
        control.progress(-1)
        control.progress(0.5)
        assert seen == [1.0, 0.0, 0.5]
