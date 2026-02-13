"""はてなブックマーク ホットエントリー取得クライアント."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import feedparser

logger = logging.getLogger("youtube_analyzer")

_BASE_URL = "https://b.hatena.ne.jp/hotentry"


def get_hotentry(category: str = "") -> list[dict]:
    """はてなブックマークのホットエントリーを取得する.

    Args:
        category: カテゴリスラッグ（"it", "social" 等）。空文字で総合。

    Returns:
        ブックマーク数降順のエントリーリスト。
        各要素: {"title", "url", "description", "bookmarks", "domain",
                 "date", "subjects", "image_url"}
    """
    if category:
        url = f"{_BASE_URL}/{category}.rss"
    else:
        url = f"{_BASE_URL}.rss"

    try:
        feed = feedparser.parse(url)
    except Exception:
        logger.exception("はてなブックマークRSS取得に失敗しました: %s", url)
        return []

    if feed.bozo and not feed.entries:
        logger.warning("はてなブックマークRSS解析エラー: %s", feed.bozo_exception)
        return []

    entries: list[dict] = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue

        link = entry.get("link", "")
        entries.append({
            "title": title,
            "url": link,
            "description": entry.get("summary", ""),
            "bookmarks": _parse_bookmark_count(entry),
            "domain": _extract_domain(link),
            "date": entry.get("published", entry.get("updated", "")),
            "subjects": [tag.term for tag in entry.get("tags", []) if hasattr(tag, "term")],
            "image_url": entry.get("hatena_imageurl", ""),
        })

    entries.sort(key=lambda e: e["bookmarks"], reverse=True)
    return entries


def _parse_bookmark_count(entry) -> int:
    """hatena_bookmarkcount を安全にint変換する."""
    raw = getattr(entry, "hatena_bookmarkcount", None)
    if raw is None:
        return 0
    try:
        return int(raw)
    except (ValueError, TypeError):
        return 0


def _extract_domain(url: str) -> str:
    """URLからドメイン名を抽出する."""
    if not url:
        return ""
    try:
        return urlparse(url).netloc
    except Exception:
        return ""
