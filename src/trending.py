"""YouTube急上昇動画からトレンドキーワードを抽出する."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd
import streamlit as st

from src.youtube_api import get_youtube_client, get_quota_tracker


# YouTube動画カテゴリ（日本）
CATEGORY_MAP = {
    "1": "映画とアニメ",
    "2": "自動車と乗り物",
    "10": "音楽",
    "15": "ペットと動物",
    "17": "スポーツ",
    "19": "旅行とイベント",
    "20": "ゲーム",
    "22": "ブログ",
    "23": "コメディ",
    "24": "エンタメ",
    "25": "ニュースと政治",
    "26": "ハウツーとスタイル",
    "27": "教育",
    "28": "科学と技術",
    "29": "NPOと社会活動",
}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_trending_videos(
    api_key: str,
    region_code: str = "JP",
    max_results: int = 50,
    category_id: str = "0",
) -> list[dict]:
    """YouTube急上昇動画を取得する（1ユニット/回）.

    Args:
        api_key: YouTube API キー
        region_code: 地域コード
        max_results: 最大取得件数（上限50）
        category_id: カテゴリID（"0"=全カテゴリ）

    Returns:
        動画情報のリスト
    """
    youtube = get_youtube_client(api_key)
    params = {
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region_code,
        "maxResults": min(max_results, 50),
    }
    if category_id != "0":
        params["videoCategoryId"] = category_id

    response = youtube.videos().list(**params).execute()
    tracker = get_quota_tracker()
    tracker.add(1)
    return response.get("items", [])


def extract_keywords_from_titles(videos: list[dict], top_n: int = 30) -> list[tuple[str, int]]:
    """動画タイトルから頻出キーワードを抽出する.

    Returns:
        [(keyword, count), ...] 頻度順
    """
    stop_words = {
        "の", "に", "は", "を", "が", "で", "と", "も", "な", "た",
        "だ", "て", "し", "する", "から", "まで", "よう", "こと",
        "ない", "いる", "ある", "この", "その", "れる", "られる",
        "THE", "the", "a", "an", "is", "it", "in", "on", "at",
        "to", "for", "of", "and", "or", "with", "by", "from",
    }

    word_counter: Counter = Counter()

    for video in videos:
        title = video.get("snippet", {}).get("title", "")
        # 日本語: 2文字以上のカタカナ・漢字の連続を抽出
        jp_words = re.findall(r"[\u4e00-\u9fff\u30a0-\u30ff]{2,}", title)
        # 英語: 2文字以上のアルファベット単語
        en_words = re.findall(r"[A-Za-z]{2,}", title)

        for w in jp_words:
            if w not in stop_words:
                word_counter[w] += 1
        for w in en_words:
            if w not in stop_words and w.upper() not in stop_words:
                word_counter[w] += 1

    return word_counter.most_common(top_n)


def analyze_trending_categories(videos: list[dict]) -> pd.DataFrame:
    """急上昇動画のカテゴリ分布を分析する.

    Returns:
        カテゴリ別の件数DataFrame
    """
    cat_counter: Counter = Counter()
    for video in videos:
        cat_id = video.get("snippet", {}).get("categoryId", "0")
        cat_name = CATEGORY_MAP.get(cat_id, f"その他({cat_id})")
        cat_counter[cat_name] += 1

    rows = [{"カテゴリ": k, "件数": v} for k, v in cat_counter.most_common()]
    return pd.DataFrame(rows)


def trending_to_dataframe(videos: list[dict]) -> pd.DataFrame:
    """急上昇動画をDataFrameに変換する."""
    rows = []
    for v in videos:
        snippet = v.get("snippet", {})
        stats = v.get("statistics", {})
        rows.append({
            "タイトル": snippet.get("title", ""),
            "チャンネル": snippet.get("channelTitle", ""),
            "再生数": int(stats.get("viewCount", 0)),
            "高評価": int(stats.get("likeCount", 0)),
            "カテゴリ": CATEGORY_MAP.get(
                snippet.get("categoryId", "0"), "その他"
            ),
            "公開日": snippet.get("publishedAt", "")[:10],
            "動画URL": f"https://www.youtube.com/watch?v={v['id']}",
        })
    return pd.DataFrame(rows)
