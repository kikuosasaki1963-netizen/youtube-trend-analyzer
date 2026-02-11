"""Streamlit 共通UIコンポーネント."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import UI_COLS_PER_ROW, UI_MAX_DISPLAY_VIDEOS
from src.utils import format_number


def extract_thumbnail_url(snippet: dict) -> str:
    """スニペットからサムネイルURLを抽出する.

    high → medium → default の優先順で取得。
    """
    thumbnails = snippet.get("thumbnails", {})
    return (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url", "")
    )


def display_video_grid_raw(
    videos: list[dict],
    max_display: int = UI_MAX_DISPLAY_VIDEOS,
    cols_per_row: int = UI_COLS_PER_ROW,
) -> None:
    """APIレスポンス形式の動画リストをサムネイルグリッドで表示する.

    急上昇トレンド・ジャンル別ランキングで使用。
    """
    for i in range(0, min(len(videos), max_display), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= min(len(videos), max_display):
                break
            v = videos[idx]
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            thumb_url = v.get("thumbnail_url") or extract_thumbnail_url(snippet)
            vid = v.get("id", "") if isinstance(v.get("id"), str) else v.get("id", "")
            view_count = v.get("view_count", int(stats.get("viewCount", 0)))

            with col:
                with st.container(border=True):
                    st.image(thumb_url, use_container_width=True)
                    vid_url = f"https://www.youtube.com/watch?v={vid}"
                    st.markdown(f"**[{snippet.get('title', '')}]({vid_url})**")
                    st.caption(
                        f"{snippet.get('channelTitle', '')} / "
                        f"{format_number(view_count)}回再生"
                    )


def display_video_grid_info(
    videos: list,
    max_display: int = UI_MAX_DISPLAY_VIDEOS,
    cols_per_row: int = UI_COLS_PER_ROW,
) -> None:
    """VideoInfo形式の動画リストをサムネイルグリッドで表示する.

    バズ動画分析で使用。
    """
    from src.utils import video_url

    for i in range(0, min(len(videos), max_display), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= min(len(videos), max_display):
                break
            v = videos[idx]
            with col:
                with st.container(border=True):
                    st.image(v.thumbnail_url, use_container_width=True)
                    st.markdown(f"**[{v.title}]({video_url(v.video_id)})**")
                    metric_cols = st.columns(3)
                    metric_cols[0].metric("V/S比率", f"{v.vs_ratio:.1f}")
                    metric_cols[1].metric("再生数", format_number(v.view_count))
                    metric_cols[2].metric("登録者", format_number(v.subscriber_count))


def csv_download_button(
    df: pd.DataFrame,
    filename: str,
    key: str,
    label: str = "CSVダウンロード",
) -> None:
    """統一されたCSVダウンロードボタンを表示する."""
    csv_data = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(label, csv_data, file_name=filename, mime="text/csv", key=key)
