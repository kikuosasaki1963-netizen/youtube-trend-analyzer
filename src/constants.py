"""アプリケーション全体で使用する定数."""

from __future__ import annotations

from typing import Optional

# ─── UI設定 ────────────────────────────────────────
UI_COLS_PER_ROW = 3
UI_MAX_DISPLAY_VIDEOS = 15

# ─── デフォルト値 ──────────────────────────────────
DEFAULT_SEARCH_QUERY = "不動産投資"
DEFAULT_REGION_CODE = "JP"

# ─── YouTube API ───────────────────────────────────
YOUTUBE_MAX_RESULTS = 50
YOUTUBE_DAILY_QUOTA_LIMIT = 10_000

# ─── キャッシュTTL（秒） ──────────────────────────
CACHE_TTL_DEFAULT = 3600

# ─── 期間オプション ────────────────────────────────
PERIOD_OPTIONS: dict[str, Optional[int]] = {
    "制限なし": None,
    "過去7日": 7,
    "過去30日": 30,
    "過去90日": 90,
    "過去1年": 365,
}

GENRE_PERIOD_OPTIONS: dict[str, int] = {
    "過去7日": 7,
    "過去30日": 30,
    "過去90日": 90,
    "過去1年": 365,
}

TREND_PERIOD_MAP: dict[str, str] = {
    "過去12ヶ月": "today 12-m",
    "過去3ヶ月": "today 3-m",
    "過去1ヶ月": "today 1-m",
    "過去7日": "now 7-d",
}
