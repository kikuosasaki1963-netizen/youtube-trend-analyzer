"""src/ui_components.py のテスト."""

from src.ui_components import extract_thumbnail_url


class TestExtractThumbnailUrl:
    def test_high_priority(self):
        snippet = {
            "thumbnails": {
                "high": {"url": "https://example.com/high.jpg"},
                "medium": {"url": "https://example.com/medium.jpg"},
                "default": {"url": "https://example.com/default.jpg"},
            }
        }
        assert extract_thumbnail_url(snippet) == "https://example.com/high.jpg"

    def test_fallback_to_medium(self):
        snippet = {
            "thumbnails": {
                "medium": {"url": "https://example.com/medium.jpg"},
                "default": {"url": "https://example.com/default.jpg"},
            }
        }
        assert extract_thumbnail_url(snippet) == "https://example.com/medium.jpg"

    def test_fallback_to_default(self):
        snippet = {
            "thumbnails": {
                "default": {"url": "https://example.com/default.jpg"},
            }
        }
        assert extract_thumbnail_url(snippet) == "https://example.com/default.jpg"

    def test_empty_thumbnails(self):
        snippet = {"thumbnails": {}}
        assert extract_thumbnail_url(snippet) == ""

    def test_no_thumbnails_key(self):
        snippet = {}
        assert extract_thumbnail_url(snippet) == ""
