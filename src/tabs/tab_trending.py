"""急上昇トレンドタブ."""

from __future__ import annotations

from src.session_keys import SessionKeys

import pandas as pd
import streamlit as st

from src.trending import (
    fetch_trending_all_categories,
    flatten_category_videos,
    extract_keywords_from_titles,
    analyze_trending_categories,
    trending_to_dataframe,
)
from src.ui_components import csv_download_button, display_video_grid_raw
from src.youtube_api import QuotaExceededError


def render(api_key: str) -> None:
    """急上昇トレンドタブを描画する."""
    st.subheader("YouTube 急上昇トレンド（日本）")
    st.caption(
        "今YouTube日本で何がバズっているかを一目で把握できます。"
        "クォータ消費: 1ユニット/回"
    )

    if st.button("急上昇データ取得（全カテゴリ）", type="primary", use_container_width=True):
        try:
            with st.spinner("全カテゴリの急上昇動画を取得中（約15ユニット消費）..."):
                category_videos = fetch_trending_all_categories(api_key)
                all_videos = flatten_category_videos(category_videos)

            st.session_state[SessionKeys.TRENDING_VIDEOS] = all_videos
            st.session_state[SessionKeys.TRENDING_BY_CATEGORY] = category_videos
        except QuotaExceededError:
            st.warning("APIクォータを超過しました。")

    if SessionKeys.TRENDING_VIDEOS in st.session_state and st.session_state[SessionKeys.TRENDING_VIDEOS]:
        trending_videos = st.session_state[SessionKeys.TRENDING_VIDEOS]
        st.success(f"{len(trending_videos)} 件の急上昇動画を取得しました")

        # バズキーワードランキング
        st.markdown("### バズキーワード TOP30")
        st.caption("急上昇動画のタイトルから頻出ワードを抽出")
        keywords = extract_keywords_from_titles(trending_videos)
        if keywords:
            kw_df = pd.DataFrame(keywords, columns=["キーワード", "出現回数"])
            col_chart, col_table = st.columns([2, 1])
            with col_chart:
                st.bar_chart(kw_df.set_index("キーワード"), horizontal=True, height=600)
            with col_table:
                st.dataframe(kw_df, use_container_width=True, height=600)

        # カテゴリ分布
        st.markdown("### カテゴリ分布")
        cat_df = analyze_trending_categories(trending_videos)
        if not cat_df.empty:
            col_pie, col_cat_table = st.columns([2, 1])
            with col_pie:
                st.bar_chart(cat_df.set_index("カテゴリ"), height=400)
            with col_cat_table:
                st.dataframe(cat_df, use_container_width=True)

        # 急上昇動画サムネイル一覧
        st.markdown("### 急上昇動画一覧")
        display_video_grid_raw(trending_videos)

        # データテーブル＆CSVダウンロード
        st.divider()
        df_trending = trending_to_dataframe(trending_videos)
        st.dataframe(df_trending, use_container_width=True, height=400)
        csv_download_button(df_trending, "youtube_trending_jp.csv", "trending_csv")
