"""YouTube Data API v3 クライアント."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import streamlit as st
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@dataclass
class VideoInfo:
    """動画情報."""

    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    thumbnail_url: str
    view_count: int = 0
    subscriber_count: int = 0
    vs_ratio: float = 0.0


@dataclass
class QuotaTracker:
    """APIクォータ使用量を追跡する."""

    used: int = 0
    daily_limit: int = 10_000

    def add(self, units: int) -> None:
        self.used += units

    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.used)

    @property
    def usage_percent(self) -> float:
        return (self.used / self.daily_limit) * 100


def get_quota_tracker() -> QuotaTracker:
    """セッション内のQuotaTrackerを取得・作成する."""
    if "quota_tracker" not in st.session_state:
        st.session_state.quota_tracker = QuotaTracker()
    return st.session_state.quota_tracker


def get_youtube_client(api_key: str):
    """YouTube Data API v3 クライアントを生成する."""
    return build("youtube", "v3", developerKey=api_key)


@st.cache_data(ttl=3600, show_spinner=False)
def search_videos(
    api_key: str,
    query: str,
    max_results: int = 50,
    published_after: str | None = None,
) -> list[dict]:
    """動画を検索する（100ユニット/回）.

    Args:
        api_key: YouTube API キー
        query: 検索クエリ
        max_results: 最大取得件数（上限50）
        published_after: ISO 8601形式の日付フィルタ

    Returns:
        検索結果のリスト
    """
    youtube = get_youtube_client(api_key)
    params = {
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": min(max_results, 50),
        "order": "viewCount",
    }
    if published_after:
        params["publishedAfter"] = published_after

    try:
        response = youtube.search().list(**params).execute()
        tracker = get_quota_tracker()
        tracker.add(100)
        return response.get("items", [])
    except HttpError as e:
        if e.resp.status == 403:
            raise QuotaExceededError("APIクォータを超過しました。明日リセットされます。") from e
        raise


@st.cache_data(ttl=3600, show_spinner=False)
def get_video_details(api_key: str, video_ids: tuple[str, ...]) -> dict[str, dict]:
    """動画の詳細情報を取得する（1ユニット/回、50件バッチ）.

    Returns:
        {video_id: {viewCount, ...}} の辞書
    """
    youtube = get_youtube_client(api_key)
    result: dict[str, dict] = {}
    tracker = get_quota_tracker()

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        try:
            response = (
                youtube.videos()
                .list(part="statistics", id=",".join(batch))
                .execute()
            )
            tracker.add(1)
            for item in response.get("items", []):
                result[item["id"]] = item["statistics"]
        except HttpError as e:
            if e.resp.status == 403:
                raise QuotaExceededError(
                    "APIクォータを超過しました。明日リセットされます。"
                ) from e
            raise

    return result


@st.cache_data(ttl=3600, show_spinner=False)
def get_channel_details(
    api_key: str, channel_ids: tuple[str, ...]
) -> dict[str, dict]:
    """チャンネルの詳細情報を取得する（1ユニット/回、50件バッチ）.

    Returns:
        {channel_id: {subscriberCount, ...}} の辞書
    """
    youtube = get_youtube_client(api_key)
    result: dict[str, dict] = {}
    tracker = get_quota_tracker()

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i : i + 50]
        try:
            response = (
                youtube.channels()
                .list(part="statistics", id=",".join(batch))
                .execute()
            )
            tracker.add(1)
            for item in response.get("items", []):
                result[item["id"]] = item["statistics"]
        except HttpError as e:
            if e.resp.status == 403:
                raise QuotaExceededError(
                    "APIクォータを超過しました。明日リセットされます。"
                ) from e
            raise

    return result


class QuotaExceededError(Exception):
    """APIクォータ超過エラー."""
