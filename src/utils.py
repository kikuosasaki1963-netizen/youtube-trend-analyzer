"""ユーティリティ関数."""


def format_number(n: int) -> str:
    """数値を読みやすい日本語表記に変換する.

    例: 1234 → "1,234", 15000 → "1.5万", 1200000 → "120万"
    """
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}億"
    if n >= 10_000:
        return f"{n / 10_000:.1f}万"
    return f"{n:,}"


def video_url(video_id: str) -> str:
    """動画IDからYouTube URLを生成する."""
    return f"https://www.youtube.com/watch?v={video_id}"


def channel_url(channel_id: str) -> str:
    """チャンネルIDからYouTube URLを生成する."""
    return f"https://www.youtube.com/channel/{channel_id}"


def truncate_text(text: str, max_length: int = 40) -> str:
    """テキストを指定文字数で切り詰める."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "…"
