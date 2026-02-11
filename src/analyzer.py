"""動画分析ロジック（V/S比率計算・フィルタ・ソート）."""

from __future__ import annotations

import pandas as pd

from src.ui_components import extract_thumbnail_url
from src.utils import video_url, channel_url
from src.youtube_api import (
    VideoInfo,
    get_channel_details,
    get_video_details,
    search_videos,
)


def fetch_and_analyze(
    api_key: str,
    query: str,
    max_results: int = 50,
    published_after: str | None = None,
) -> list[VideoInfo]:
    """検索 → 動画詳細 → チャンネル詳細 → V/S比率計算を一括実行する.

    Args:
        api_key: YouTube API キー
        query: 検索クエリ
        max_results: 最大取得件数
        published_after: ISO 8601形式の日付フィルタ

    Returns:
        VideoInfo のリスト（V/S比率計算済み）
    """
    # Step 1: 検索
    search_results = search_videos(api_key, query, max_results, published_after)
    if not search_results:
        return []

    # Step 2: 検索結果からID・基本情報を抽出
    videos, video_ids, channel_ids_set = _extract_search_info(search_results)

    # Step 3: 動画・チャンネル統計情報を取得
    video_stats = get_video_details(api_key, tuple(video_ids))
    channel_stats = get_channel_details(api_key, tuple(channel_ids_set))

    # Step 4: V/S比率計算
    _calculate_vs_ratios(videos, video_stats, channel_stats)

    return videos


def _extract_search_info(
    search_results: list[dict],
) -> tuple[list[VideoInfo], list[str], set[str]]:
    """検索結果からVideoInfo・動画ID・チャンネルIDを抽出する."""
    videos: list[VideoInfo] = []
    video_ids: list[str] = []
    channel_ids_set: set[str] = set()

    for item in search_results:
        snippet = item["snippet"]
        vid = item["id"]["videoId"]
        video_ids.append(vid)
        channel_ids_set.add(snippet["channelId"])
        videos.append(
            VideoInfo(
                video_id=vid,
                title=snippet.get("title", ""),
                channel_id=snippet["channelId"],
                channel_title=snippet.get("channelTitle", ""),
                published_at=snippet.get("publishedAt", ""),
                thumbnail_url=extract_thumbnail_url(snippet),
            )
        )

    return videos, video_ids, channel_ids_set


def _calculate_vs_ratios(
    videos: list[VideoInfo],
    video_stats: dict[str, dict],
    channel_stats: dict[str, dict],
) -> None:
    """動画リストにV/S比率を計算・設定する（in-place）."""
    for v in videos:
        stats = video_stats.get(v.video_id, {})
        v.view_count = int(stats.get("viewCount", 0))

        ch_stats = channel_stats.get(v.channel_id, {})
        if ch_stats.get("hiddenSubscriberCount", False):
            v.subscriber_count = 0
        else:
            v.subscriber_count = int(ch_stats.get("subscriberCount", 0))

        if v.subscriber_count > 0:
            v.vs_ratio = v.view_count / v.subscriber_count
        else:
            v.vs_ratio = 0.0


def filter_videos(
    videos: list[VideoInfo],
    max_subscribers: int | None = None,
    min_views: int | None = None,
    min_vs_ratio: float | None = None,
) -> list[VideoInfo]:
    """動画リストをフィルタリングする.

    Args:
        videos: フィルタ対象のVideoInfoリスト
        max_subscribers: 登録者数上限
        min_views: 再生数下限
        min_vs_ratio: V/S比率下限

    Returns:
        フィルタ適用後のVideoInfoリスト
    """
    result = videos
    if max_subscribers is not None:
        result = [v for v in result if v.subscriber_count <= max_subscribers]
    if min_views is not None:
        result = [v for v in result if v.view_count >= min_views]
    if min_vs_ratio is not None:
        result = [v for v in result if v.vs_ratio >= min_vs_ratio]
    return result


def sort_by_vs_ratio(videos: list[VideoInfo], descending: bool = True) -> list[VideoInfo]:
    """V/S比率でソートする."""
    return sorted(videos, key=lambda v: v.vs_ratio, reverse=descending)


def videos_to_dataframe(videos: list[VideoInfo]) -> pd.DataFrame:
    """VideoInfoリストをDataFrameに変換する."""
    rows = []
    for v in videos:
        rows.append(
            {
                "タイトル": v.title,
                "チャンネル": v.channel_title,
                "再生数": v.view_count,
                "登録者数": v.subscriber_count,
                "V/S比率": round(v.vs_ratio, 2),
                "公開日": v.published_at[:10] if v.published_at else "",
                "動画URL": video_url(v.video_id),
                "チャンネルURL": channel_url(v.channel_id),
            }
        )
    return pd.DataFrame(rows)
