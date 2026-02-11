"""バズ動画分析（V/S比率）タブ."""

from __future__ import annotations

from src.session_keys import SessionKeys

from datetime import datetime, timedelta

import streamlit as st

from src.analyzer import (
    fetch_and_analyze,
    filter_videos,
    sort_by_vs_ratio,
    videos_to_dataframe,
)
from src.ui_components import csv_download_button, display_video_grid_info
from src.youtube_api import QuotaExceededError


def render(
    api_key: str,
    search_query: str,
    max_subscribers: int,
    min_views: int,
    min_vs_ratio: float,
    period_days: int | None,
) -> None:
    """バズ動画分析タブを描画する."""
    st.subheader("バズ動画分析（V/S比率）")
    st.caption("V/S比率 = 再生数 / 登録者数。高いほど企画力のある動画です。")

    if st.button("分析開始", type="primary", use_container_width=True):
        if not search_query:
            st.warning("サイドバーで検索キーワードを入力してください。")
        else:
            published_after = None
            if period_days:
                dt = datetime.utcnow() - timedelta(days=period_days)
                published_after = dt.strftime("%Y-%m-%dT%H:%M:%SZ")

            try:
                with st.spinner("YouTube APIから動画を検索中..."):
                    videos = fetch_and_analyze(
                        api_key, search_query, published_after=published_after
                    )

                filtered = filter_videos(
                    videos,
                    max_subscribers=max_subscribers if max_subscribers > 0 else None,
                    min_views=min_views if min_views > 0 else None,
                    min_vs_ratio=min_vs_ratio if min_vs_ratio > 0 else None,
                )

                sorted_videos = sort_by_vs_ratio(filtered)
                st.session_state[SessionKeys.ANALYZED_VIDEOS] = sorted_videos

            except QuotaExceededError:
                st.warning(
                    "APIクォータを超過しました。"
                    "クォータは太平洋時間の午前0時（日本時間16:00）にリセットされます。"
                )

    # 結果表示
    if SessionKeys.ANALYZED_VIDEOS in st.session_state and st.session_state[SessionKeys.ANALYZED_VIDEOS]:
        sorted_videos = st.session_state[SessionKeys.ANALYZED_VIDEOS]
        st.success(f"{len(sorted_videos)} 件の動画が見つかりました")

        display_video_grid_info(sorted_videos, max_display=len(sorted_videos))

        st.divider()
        df = videos_to_dataframe(sorted_videos)
        st.dataframe(df, use_container_width=True, height=400)
        csv_download_button(df, f"buzz_videos_{search_query}.csv", "buzz_csv")

    elif SessionKeys.ANALYZED_VIDEOS in st.session_state:
        st.info(
            "条件に一致する動画が見つかりませんでした。"
            "フィルタ条件を緩めてお試しください。"
        )
