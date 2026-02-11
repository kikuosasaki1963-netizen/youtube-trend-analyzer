"""src/utils.py のテスト."""

from src.utils import format_number, video_url, channel_url, truncate_text


class TestFormatNumber:
    def test_small_number(self):
        assert format_number(999) == "999"

    def test_thousands(self):
        assert format_number(1234) == "1,234"

    def test_ten_thousand(self):
        assert format_number(15000) == "1.5万"

    def test_hundred_thousand(self):
        assert format_number(123456) == "12.3万"

    def test_million(self):
        assert format_number(1_200_000) == "120.0万"

    def test_hundred_million(self):
        assert format_number(150_000_000) == "1.5億"

    def test_zero(self):
        assert format_number(0) == "0"


class TestVideoUrl:
    def test_basic(self):
        assert video_url("abc123") == "https://www.youtube.com/watch?v=abc123"


class TestChannelUrl:
    def test_basic(self):
        assert channel_url("UCxyz") == "https://www.youtube.com/channel/UCxyz"


class TestTruncateText:
    def test_short_text(self):
        assert truncate_text("short", 40) == "short"

    def test_exact_length(self):
        text = "a" * 40
        assert truncate_text(text, 40) == text

    def test_long_text(self):
        text = "a" * 50
        result = truncate_text(text, 40)
        assert len(result) == 40
        assert result.endswith("…")
