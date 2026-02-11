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

# ─── Google Trends カテゴリ ────────────────────────
GOOGLE_TRENDS_CATEGORIES: dict[str, int] = {
    "全体": 0,
    "エンターテインメント": 3,
    "コンピュータ・電子機器": 5,
    "金融": 7,
    "ビジネス": 12,
    "ニュース": 16,
    "ショッピング": 18,
    "スポーツ": 20,
    "不動産": 29,
    "美容・フィットネス": 44,
    "健康": 45,
    "自動車": 47,
    "趣味・レジャー": 65,
    "旅行": 67,
    "フード・ドリンク": 71,
    "科学": 174,
    "仕事・教育": 958,
}

GOOGLE_TRENDS_TIMEFRAMES: dict[str, str] = {
    "過去12ヶ月": "today 12-m",
    "過去3ヶ月": "today 3-m",
}
