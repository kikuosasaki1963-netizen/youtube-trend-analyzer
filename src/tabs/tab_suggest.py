"""サジェストキーワード収集タブ."""

from __future__ import annotations

from src.session_keys import SessionKeys

import pandas as pd
import streamlit as st

from src.suggest_api import (
    fetch_suggestions,
    fetch_suggestions_with_alphabet_soup,
    flatten_unique_suggestions,
)
from src.ui_components import csv_download_button


def render(search_query: str) -> None:
    """サジェストキーワード収集タブを描画する."""
    st.subheader("サジェストキーワード収集")
    st.caption(
        "Googleサジェスト非公式APIを使って、関連キーワードを網羅的に取得します。"
    )

    col_base, col_soup = st.columns(2)

    with col_base:
        if st.button("基本サジェスト取得", use_container_width=True):
            if not search_query:
                st.warning("検索キーワードを入力してください。")
            else:
                with st.spinner("サジェスト取得中..."):
                    suggestions = fetch_suggestions(search_query)
                st.session_state[SessionKeys.BASE_SUGGESTIONS] = suggestions

    with col_soup:
        if st.button("アルファベットスープ取得（約2分）", use_container_width=True):
            if not search_query:
                st.warning("検索キーワードを入力してください。")
            else:
                progress_bar = st.progress(0, text="サジェスト収集中...")

                def update_progress(current: int, total: int) -> None:
                    progress_bar.progress(
                        current / total,
                        text=f"サジェスト収集中... ({current}/{total})",
                    )

                soup_results = fetch_suggestions_with_alphabet_soup(
                    search_query,
                    delay=1.5,
                    progress_callback=update_progress,
                )
                progress_bar.empty()

                base = st.session_state.get(SessionKeys.BASE_SUGGESTIONS, [])
                if not base:
                    base = fetch_suggestions(search_query)
                    st.session_state[SessionKeys.BASE_SUGGESTIONS] = base

                all_keywords = flatten_unique_suggestions(base, soup_results)
                st.session_state[SessionKeys.ALL_SUGGESTIONS] = all_keywords

    # 結果表示
    if SessionKeys.ALL_SUGGESTIONS in st.session_state and st.session_state[SessionKeys.ALL_SUGGESTIONS]:
        keywords = st.session_state[SessionKeys.ALL_SUGGESTIONS]
        st.success(f"{len(keywords)} 件のユニークキーワードを取得しました")

        df_kw = pd.DataFrame({"キーワード": keywords})
        st.dataframe(df_kw, use_container_width=True, height=400)
        csv_download_button(
            df_kw, f"suggestions_{search_query}.csv", "suggest_csv",
        )

    elif SessionKeys.BASE_SUGGESTIONS in st.session_state and st.session_state[SessionKeys.BASE_SUGGESTIONS]:
        suggestions = st.session_state[SessionKeys.BASE_SUGGESTIONS]
        st.info(f"{len(suggestions)} 件の基本サジェストを取得しました")

        df_base = pd.DataFrame({"キーワード": suggestions})
        st.dataframe(df_base, use_container_width=True)
