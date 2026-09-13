"""格式化器测试（按新的结构化章节输入重写）。"""

from core.formatters import format_result, output_filename
from core.models import BookMetadata, Chapter, ExtractionResult


def _result(title=None, author=None, chapters=None):
    meta = BookMetadata(path="/a/book.epub", fmt="epub", title=title, author=author)
    return ExtractionResult(metadata=meta, chapters=chapters or [Chapter(text="正文内容")])


class TestOutputFilename:
    def test_extensions(self):
        assert output_filename("/a/book.epub", "txt") == "book.txt"
        assert output_filename("/a/book.epub", "md") == "book.md"
        assert output_filename("/a/book.epub", "html") == "book.html"
        assert output_filename("/a/book.epub", "epub") == "book.epub"


class TestTxtFormatter:
    def test_plain_body(self):
        content, name = format_result(_result(), "txt", "/a/book.epub")
        assert content == "正文内容"
        assert name == "book.txt"

    def test_metadata_header(self):
        result = _result(title="测试书", author="作者A")
        content, _ = format_result(result, "txt", "/a/book.epub")
        assert content.startswith("书名：测试书\n作者：作者A\n---")
        assert "正文内容" in content

    def test_chapter_titles(self):
        result = _result(chapters=[Chapter(title="第一章", text="甲"), Chapter(title="第二章", text="乙")])
        content, _ = format_result(result, "txt", "/a/book.epub")
        assert "第一章" in content and "第二章" in content
        assert content.index("第一章") < content.index("甲") < content.index("第二章")


class TestMdFormatter:
    def test_book_and_chapter_headings(self):
        result = _result(title="书名X", author="作者B", chapters=[Chapter(title="第一章", text="甲乙")])
        content, name = format_result(result, "md", "/a/book.epub")
        assert name == "book.md"
        assert "# 书名X" in content
        assert "## 第一章" in content
        assert "甲乙" in content
        assert content.startswith("# 书名X")

    def test_no_metadata(self):
        content, _ = format_result(_result(), "md", "/a/book.epub")
        assert content.strip() == "正文内容"


class TestHtmlFormatter:
    def test_basic_structure(self):
        content, name = format_result(_result(), "html", "/a/book.epub")
        assert "<!DOCTYPE html>" in content
        assert "正文内容" in content
        assert name == "book.html"

    def test_metadata_div_and_chapter_heading(self):
        result = _result(title="测试书", author="作者A", chapters=[Chapter(title="第一章", text="甲")])
        content, _ = format_result(result, "html", "/a/book.epub")
        assert 'class="metadata"' in content
        assert "测试书" in content
        assert "作者A" in content
        assert "<h2>第一章</h2>" in content

    def test_html_escaped(self):
        result = _result(chapters=[Chapter(text="<script>alert(1)</script>")])
        content, _ = format_result(result, "html", "/a/book.epub")
        assert "<script>alert(1)</script>" not in content
        assert "&lt;script&gt;" in content


class TestUniqueOutputPath:
    def test_no_conflict(self, tmp_path):
        from core.engine import unique_output_path

        assert unique_output_path(str(tmp_path), "book.txt") == tmp_path / "book.txt"

    def test_conflict_appends_counter(self, tmp_path):
        from core.engine import unique_output_path

        (tmp_path / "book.txt").write_text("x")
        (tmp_path / "book (2).txt").write_text("x")
        assert unique_output_path(str(tmp_path), "book.txt") == tmp_path / "book (3).txt"
