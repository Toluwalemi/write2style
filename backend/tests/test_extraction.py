import pytest
from fastapi import HTTPException

from app.extraction import chunk_text, extract_text


class TestExtractText:
    def test_plain_text_by_extension(self):
        result = extract_text("notes.txt", "", b"hello world")
        assert result == "hello world"

    def test_markdown_by_extension(self):
        result = extract_text("post.md", "", b"# Title\n\nbody")
        assert result == "# Title\n\nbody"

    def test_text_by_content_type(self):
        result = extract_text("unknown", "text/plain", b"abc")
        assert result == "abc"

    def test_invalid_utf8_replaced(self):
        result = extract_text("a.txt", "", b"\xff\xfe valid")
        assert "valid" in result

    def test_unsupported_raises_415(self):
        with pytest.raises(HTTPException) as exc:
            extract_text("image.png", "image/png", b"\x89PNG")
        assert exc.value.status_code == 415


class TestChunkText:
    def test_empty_returns_empty(self):
        assert chunk_text("", 100, 10) == []
        assert chunk_text("   \n  ", 100, 10) == []

    def test_short_text_single_chunk(self):
        assert chunk_text("hello", 100, 10) == ["hello"]

    def test_long_text_multiple_chunks(self):
        text = "a" * 250
        chunks = chunk_text(text, 100, 20)
        assert len(chunks) >= 3
        assert all(len(c) <= 100 for c in chunks)

    def test_overlap_creates_shared_content(self):
        text = "abcdefghij" * 20  # 200 chars
        chunks = chunk_text(text, 50, 10)
        assert len(chunks) > 1

    def test_strips_whitespace(self):
        chunks = chunk_text("  hello  ", 100, 10)
        assert chunks == ["hello"]
