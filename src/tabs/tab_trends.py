"""トレンド調査（Google Trends）タブ."""

from __future__ import annotations

from src.session_keys import SessionKeys

import pandas as pd
import streamlit as st

from src.constants import TREND_PERIOD_MAP
from src.trends_api import (
    get_trending_searches,
    get_interest_over_time,
    get_related_queries,
)
from src.ui_components import csv_download_button


def render(search_query: str) -> None:
    """トレンド調査タブを描画する."""
    st.subheader("トレンド調査")
    st.caption(
        "Google Trends のデータから、今注目されている検索キーワードを確認できます。"
        "APIクォータ消費なし。"
    )

    _render_trending_searches()
    st.divider()
    _render_interest_over_time(search_query)


def _render_trending_searches() -> None:
    """急上昇検索ワードセクションを描画する."""
    st.markdown("### 今日の急上昇検索ワード（日本）")
    st.caption(
        "Google検索で今日急上昇しているキーワードTOP10と関連ニュース。"
        "キーワード指定不要。"
    )

    if st.button("急上昇ワードを取得", use_container_width=True, key="trending_searches_btn"):
        try:
            with st.spinner("Google Trends 急上昇ワードを取得中..."):
                trending_data = get_trending_searches(geo="JP")
            st.session_state[SessionKeys.TRENDING_SEARCHES] = trending_data
        except Exception as e:
            st.error(f"取得に失敗しました: {e}")

    if SessionKeys.TRENDING_SEARCHES not in st.session_state:
        return

    trending_data = st.session_state[SessionKeys.TRENDING_SEARCHES]
    if not trending_data:
        st.info("急上昇ワードが取得できませんでした。")
        return

    st.success(f"{len(trending_data)} 件の急上昇ワードを取得")

    for rank, item in enumerate(trending_data, 1):
        with st.container(border=True):
            col_rank, col_info = st.columns([1, 6])
            with col_rank:
                st.markdown(f"## {rank}")
                st.caption(item["traffic"])
            with col_info:
                st.markdown(f"### {item['keyword']}")
                for news in item.get("news", [])[:2]:
                    st.markdown(
                        f"- [{news['title']}]({news['url']})\u3000"
                        f"*{news['source']}*"
                    )

    # CSVダウンロード
    csv_rows = []
    for rank, item in enumerate(trending_data, 1):
        csv_rows.append({
            "順位": rank,
            "キーワード": item["keyword"],
            "検索ボリューム": item["traffic"],
            "関連ニュース": " / ".join(
                n["title"] for n in item.get("news", [])[:2]
            ),
        })
    df_csv = pd.DataFrame(csv_rows)
    csv_download_button(
        df_csv, "google_trending_searches_jp.csv", "trending_searches_csv",
    )


def _render_interest_over_time(search_query: str) -> None:
    """キーワード別検索ボリューム調査セクションを描画する."""
    st.markdown("### キーワード別 検索ボリューム調査")
    st.caption("特定キーワードの検索ボリューム推移と関連キーワードを表示します。")

    trend_period = st.selectbox(
        "調査期間",
        options=list(TREND_PERIOD_MAP.keys()),
        key="trend_period",
    )

    if st.button("トレンド調査開始", type="primary", use_container_width=True):
        if not search_query:
            st.warning("サイドバーで検索キーワードを入力してください。")
        else:
            try:
                with st.spinner("Google Trends データ取得中..."):
                    timeframe = TREND_PERIOD_MAP[trend_period]
                    interest_df = get_interest_over_time(
                        search_query, timeframe=timeframe,
                    )
                    related = get_related_queries(search_query)

                st.session_state[SessionKeys.TREND_INTEREST] = interest_df
                st.session_state[SessionKeys.TREND_RELATED] = related
                st.session_state[SessionKeys.TREND_KEYWORD] = search_query

            except Exception as e:
                st.error(f"データ取得に失敗しました: {e}")

    if SessionKeys.TREND_INTEREST not in st.session_state or not st.session_state.get(SessionKeys.TREND_KEYWORD):
        return

    kw = st.session_state[SessionKeys.TREND_KEYWORD]
    interest_df = st.session_state[SessionKeys.TREND_INTEREST]
    related = st.session_state[SessionKeys.TREND_RELATED]

    # 検索ボリューム推移グラフ
    st.markdown(f"### 「{kw}」の検索人気度推移")
    if not interest_df.empty:
        peak_val = int(interest_df[kw].max())
        peak_date = interest_df[kw].idxmax().strftime("%Y-%m-%d")
        current_val = int(interest_df[kw].iloc[-1])

        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("ピーク日", peak_date)
        col_m2.metric("ピーク値", f"{peak_val}（= 100%）")
        col_m3.metric("現在の人気度", f"{current_val}")

        st.line_chart(interest_df[kw], use_container_width=True, height=300)
        st.caption(
            "※ 数値はGoogle Trendsの**相対的な人気度**（0〜100）です。"
            "100 = 期間内で最も検索された時点。"
            "実際の検索回数はGoogleが非公開のため取得できません。"
        )
    else:
        st.info("この期間のデータがありません。")

    # 関連キーワード
    col_rising, col_top = st.columns(2)

    with col_rising:
        st.markdown("### 急上昇キーワード")
        rising_df = related.get("rising", pd.DataFrame())
        if not rising_df.empty:
            st.dataframe(rising_df, use_container_width=True, height=400)
        else:
            st.info("急上昇キーワードが見つかりませんでした。")

    with col_top:
        st.markdown("### 人気キーワード")
        top_df = related.get("top", pd.DataFrame())
        if not top_df.empty:
            st.dataframe(top_df, use_container_width=True, height=400)
        else:
            st.info("人気キーワードが見つかりませんでした。")
