"""src/hatena_api.py のテスト."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from src.hatena_api import get_hotentry, _parse_bookmark_count, _extract_domain


# ─── ヘルパー ─────────────────────────────────────────

def _make_feed(entries=None, bozo=False, bozo_exception=None):
    """feedparser.parse() の戻り値を模擬する."""
    feed = SimpleNamespace()
    feed.entries = entries or []
    feed.bozo = bozo
    feed.bozo_exception = bozo_exception
    return feed


def _make_entry(
    title: str = "テスト記事",
    link: str = "https://example.com/article",
    summary: str = "記事の概要",
    bookmarkcount: str = "100",
    published: str = "2026-01-15T12:00:00+09:00",
    tags=None,
    imageurl: str = "",
):
    """feedparserエントリーを模擬する."""
    entry = SimpleNamespace()
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.hatena_bookmarkcount = bookmarkcount
    entry.published = published
    entry.hatena_imageurl = imageurl
    entry.tags = tags or []

    def get(key, default=""):
        return getattr(entry, key, default)
    entry.get = get

    return entry


# ─── TestGetHotentry ──────────────────────────────────

class TestGetHotentry:
    @patch("src.hatena_api.feedparser.parse")
    def test_success(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[
            _make_entry(title="記事A", bookmarkcount="200"),
            _make_entry(title="記事B", bookmarkcount="500"),
        ])
        result = get_hotentry()
        assert len(result) == 2
        assert result[0]["title"] == "記事B"
        assert result[0]["bookmarks"] == 500
        assert result[1]["title"] == "記事A"
        assert result[1]["bookmarks"] == 200

    @patch("src.hatena_api.feedparser.parse")
    def test_all_categories(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[
            _make_entry(title="IT記事"),
        ])
        for slug in ["", "it", "social", "economics", "life", "entertainment", "game", "fun", "knowledge"]:
            result = get_hotentry(slug)
            assert isinstance(result, list)

    @patch("src.hatena_api.feedparser.parse")
    def test_empty(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[])
        result = get_hotentry()
        assert result == []

    @patch("src.hatena_api.feedparser.parse")
    def test_bozo_error_with_no_entries(self, mock_parse):
        mock_parse.return_value = _make_feed(
            entries=[], bozo=True, bozo_exception=Exception("parse error"),
        )
        result = get_hotentry()
        assert result == []

    @patch("src.hatena_api.feedparser.parse")
    def test_exception(self, mock_parse):
        mock_parse.side_effect = Exception("network error")
        result = get_hotentry()
        assert result == []

    @patch("src.hatena_api.feedparser.parse")
    def test_sorted_by_bookmarks(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[
            _make_entry(title="少ない", bookmarkcount="10"),
            _make_entry(title="多い", bookmarkcount="999"),
            _make_entry(title="中間", bookmarkcount="100"),
        ])
        result = get_hotentry()
        assert [e["bookmarks"] for e in result] == [999, 100, 10]

    @patch("src.hatena_api.feedparser.parse")
    def test_skip_without_title(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[
            _make_entry(title=""),
            _make_entry(title="   "),
            _make_entry(title="有効な記事"),
        ])
        result = get_hotentry()
        assert len(result) == 1
        assert result[0]["title"] == "有効な記事"

    @patch("src.hatena_api.feedparser.parse")
    def test_domain_extraction(self, mock_parse):
        mock_parse.return_value = _make_feed(entries=[
            _make_entry(link="https://www.example.com/path/to/article"),
        ])
        result = get_hotentry()
        assert result[0]["domain"] == "www.example.com"


# ─── TestParseBookmarkCount ───────────────────────────

class TestParseBookmarkCount:
    def test_valid(self):
        entry = SimpleNamespace(hatena_bookmarkcount="42")
        assert _parse_bookmark_count(entry) == 42

    def test_zero(self):
        entry = SimpleNamespace(hatena_bookmarkcount="0")
        assert _parse_bookmark_count(entry) == 0

    def test_missing(self):
        entry = SimpleNamespace()
        assert _parse_bookmark_count(entry) == 0

    def test_invalid(self):
        entry = SimpleNamespace(hatena_bookmarkcount="abc")
        assert _parse_bookmark_count(entry) == 0

    def test_none(self):
        entry = SimpleNamespace(hatena_bookmarkcount=None)
        assert _parse_bookmark_count(entry) == 0


# ─── TestExtractDomain ────────────────────────────────

class TestExtractDomain:
    def test_normal(self):
        assert _extract_domain("https://example.com/path") == "example.com"

    def test_subdomain(self):
        assert _extract_domain("https://blog.example.com/article") == "blog.example.com"

    def test_empty(self):
        assert _extract_domain("") == ""

    def test_invalid(self):
        assert _extract_domain("not-a-url") == ""
