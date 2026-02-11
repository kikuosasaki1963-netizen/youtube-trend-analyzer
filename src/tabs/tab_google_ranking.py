"""Google検索ワードランキングタブ."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import GOOGLE_TRENDS_CATEGORIES, GOOGLE_TRENDS_TIMEFRAMES
from src.session_keys import SessionKeys
from src.trends_api import get_category_related_queries, get_category_related_topics
from src.ui_components import csv_download_button


def render() -> None:
    """Google検索ワードランキングタブを描画する."""
    st.subheader("Google検索ワードランキング")
    st.caption("Google検索全体のキーワードを全体・ジャンル別でランキング表示します")

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "ジャンル",
            options=list(GOOGLE_TRENDS_CATEGORIES.keys()),
            key="google_ranking_category_select",
        )
    with col2:
        timeframe_label = st.selectbox(
            "期間",
            options=list(GOOGLE_TRENDS_TIMEFRAMES.keys()),
            key="google_ranking_timeframe_select",
        )

    if st.button("ランキングを取得", type="primary", use_container_width=True, key="google_ranking_btn"):
        cat_id = GOOGLE_TRENDS_CATEGORIES[category]
        timeframe = GOOGLE_TRENDS_TIMEFRAMES[timeframe_label]
        try:
            with st.spinner("Google Trends データ取得中..."):
                queries = get_category_related_queries(cat=cat_id, timeframe=timeframe)
                topics = get_category_related_topics(cat=cat_id, timeframe=timeframe)

            st.session_state[SessionKeys.GOOGLE_RANKING_QUERIES] = queries
            st.session_state[SessionKeys.GOOGLE_RANKING_TOPICS] = topics
            st.session_state[SessionKeys.GOOGLE_RANKING_CATEGORY] = category
        except Exception as e:
            st.error(f"データ取得に失敗しました: {e}")

    if SessionKeys.GOOGLE_RANKING_QUERIES not in st.session_state:
        return

    queries = st.session_state[SessionKeys.GOOGLE_RANKING_QUERIES]
    topics = st.session_state[SessionKeys.GOOGLE_RANKING_TOPICS]
    cat_label = st.session_state.get(SessionKeys.GOOGLE_RANKING_CATEGORY, "全体")

    st.markdown(f"### 「{cat_label}」カテゴリのランキング")

    # 検索ワード: 人気 / 急上昇
    col_top_q, col_rising_q = st.columns(2)

    with col_top_q:
        st.markdown("#### 人気クエリ TOP")
        top_q = queries.get("top", pd.DataFrame())
        if not top_q.empty:
            st.dataframe(top_q, use_container_width=True, height=400)
        else:
            st.info("人気クエリが見つかりませんでした。")

    with col_rising_q:
        st.markdown("#### 急上昇クエリ TOP")
        rising_q = queries.get("rising", pd.DataFrame())
        if not rising_q.empty:
            st.dataframe(rising_q, use_container_width=True, height=400)
        else:
            st.info("急上昇クエリが見つかりませんでした。")

    st.divider()

    # トピック: 人気 / 急上昇
    col_top_t, col_rising_t = st.columns(2)

    with col_top_t:
        st.markdown("#### 人気トピック TOP")
        top_t = topics.get("top", pd.DataFrame())
        if not top_t.empty:
            st.dataframe(top_t, use_container_width=True, height=400)
        else:
            st.info("人気トピックが見つかりませんでした。")

    with col_rising_t:
        st.markdown("#### 急上昇トピック TOP")
        rising_t = topics.get("rising", pd.DataFrame())
        if not rising_t.empty:
            st.dataframe(rising_t, use_container_width=True, height=400)
        else:
            st.info("急上昇トピックが見つかりませんでした。")

    # CSVダウンロード
    _render_csv_downloads(queries, topics, cat_label)


def _render_csv_downloads(
    queries: dict[str, pd.DataFrame],
    topics: dict[str, pd.DataFrame],
    cat_label: str,
) -> None:
    """CSVダウンロードボタンを表示する."""
    st.divider()
    st.markdown("#### CSVダウンロード")

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    with col_d1:
        top_q = queries.get("top", pd.DataFrame())
        if not top_q.empty:
            csv_download_button(
                top_q,
                f"google_ranking_top_queries_{cat_label}.csv",
                "google_ranking_top_queries_csv",
                label="人気クエリ",
            )

    with col_d2:
        rising_q = queries.get("rising", pd.DataFrame())
        if not rising_q.empty:
            csv_download_button(
                rising_q,
                f"google_ranking_rising_queries_{cat_label}.csv",
                "google_ranking_rising_queries_csv",
                label="急上昇クエリ",
            )

    with col_d3:
        top_t = topics.get("top", pd.DataFrame())
        if not top_t.empty:
            csv_download_button(
                top_t,
                f"google_ranking_top_topics_{cat_label}.csv",
                "google_ranking_top_topics_csv",
                label="人気トピック",
            )

    with col_d4:
        rising_t = topics.get("rising", pd.DataFrame())
        if not rising_t.empty:
            csv_download_button(
                rising_t,
                f"google_ranking_rising_topics_{cat_label}.csv",
                "google_ranking_rising_topics_csv",
                label="急上昇トピック",
            )
