"""SNSバズニュースタブ."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.constants import HATENA_CATEGORIES
from src.hatena_api import get_hotentry
from src.session_keys import SessionKeys
from src.trends_api import get_trending_searches
from src.ui_components import csv_download_button


def render() -> None:
    """SNSバズニュースタブを描画する."""
    st.subheader("SNSバズニュース")
    st.caption(
        "はてなブックマークとGoogle Trendsから、今バズっている記事・ニュースをランキング形式で表示します。"
        "APIキー不要で利用できます。"
    )

    _render_hatena_section()
    st.divider()
    _render_google_trending_news_section()


def _render_hatena_section() -> None:
    """はてなブックマーク ホットエントリーセクション."""
    st.markdown("### はてなブックマーク ホットエントリー")
    st.caption("はてなブックマークで話題の記事をブックマーク数順にランキング表示します。")

    category_label = st.selectbox(
        "カテゴリ",
        options=list(HATENA_CATEGORIES.keys()),
        key="hatena_category_select",
    )
    category_slug = HATENA_CATEGORIES[category_label]

    if st.button("ホットエントリー取得", type="primary", use_container_width=True, key="hatena_fetch"):
        with st.spinner("はてなブックマーク ホットエントリーを取得中..."):
            entries = get_hotentry(category_slug)
        st.session_state[SessionKeys.SNS_BUZZ_HATENA] = entries
        st.session_state[SessionKeys.SNS_BUZZ_HATENA_CATEGORY] = category_label

    if SessionKeys.SNS_BUZZ_HATENA in st.session_state and st.session_state[SessionKeys.SNS_BUZZ_HATENA]:
        entries = st.session_state[SessionKeys.SNS_BUZZ_HATENA]
        cat_label = st.session_state.get(SessionKeys.SNS_BUZZ_HATENA_CATEGORY, "総合")
        st.success(f"「{cat_label}」カテゴリから {len(entries)} 件のエントリーを取得しました")

        for rank, entry in enumerate(entries, 1):
            with st.container(border=True):
                col_rank, col_content, col_stats = st.columns([0.5, 6, 1.5])
                with col_rank:
                    st.markdown(f"### {rank}")
                with col_content:
                    st.markdown(f"**[{entry['title']}]({entry['url']})**")
                    if entry["description"]:
                        st.caption(entry["description"][:120])
                with col_stats:
                    st.metric("Bookmarks", f"{entry['bookmarks']:,}")
                    st.caption(entry["domain"])

        st.divider()
        df = _hatena_entries_to_dataframe(entries)
        st.dataframe(df, use_container_width=True, height=400)
        csv_download_button(df, "hatena_hotentry.csv", "hatena_csv")


def _render_google_trending_news_section() -> None:
    """Google Trends 急上昇ニュースセクション."""
    st.markdown("### Google Trends 急上昇ニュース")
    st.caption("Google Trendsの急上昇キーワードに関連するニュース記事を一覧表示します。")

    if st.button("急上昇ニュース取得", type="primary", use_container_width=True, key="trending_news_fetch"):
        with st.spinner("Google Trends 急上昇ニュースを取得中..."):
            trending_data = get_trending_searches()
        news_items = _flatten_trending_news(trending_data)
        st.session_state[SessionKeys.SNS_BUZZ_TRENDING] = news_items

    if SessionKeys.SNS_BUZZ_TRENDING in st.session_state and st.session_state[SessionKeys.SNS_BUZZ_TRENDING]:
        news_items = st.session_state[SessionKeys.SNS_BUZZ_TRENDING]
        st.success(f"{len(news_items)} 件の関連ニュースを取得しました")

        for rank, item in enumerate(news_items, 1):
            with st.container(border=True):
                col_rank, col_content, col_stats = st.columns([0.5, 6, 1.5])
                with col_rank:
                    st.markdown(f"### {rank}")
                with col_content:
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    st.caption(f"関連キーワード: {item['keyword']}")
                with col_stats:
                    st.metric("検索Vol", item["traffic"])
                    st.caption(item["source"])

        st.divider()
        df = _trending_news_to_dataframe(news_items)
        st.dataframe(df, use_container_width=True, height=400)
        csv_download_button(df, "google_trending_news.csv", "trending_news_csv")


def _flatten_trending_news(trending_data: list[dict]) -> list[dict]:
    """ネストされたニュースを1次元リストに展開する."""
    items: list[dict] = []
    for trend in trending_data:
        keyword = trend.get("keyword", "")
        traffic = trend.get("traffic", "")
        for news in trend.get("news", []):
            title = news.get("title", "").strip()
            if not title:
                continue
            items.append({
                "title": title,
                "url": news.get("url", ""),
                "source": news.get("source", ""),
                "keyword": keyword,
                "traffic": traffic,
            })
    return items


def _hatena_entries_to_dataframe(entries: list[dict]) -> pd.DataFrame:
    """はてなエントリーリストをDataFrameに変換する."""
    if not entries:
        return pd.DataFrame()
    rows = []
    for rank, e in enumerate(entries, 1):
        rows.append({
            "順位": rank,
            "タイトル": e["title"],
            "URL": e["url"],
            "ブックマーク数": e["bookmarks"],
            "ドメイン": e["domain"],
            "日付": e["date"],
            "タグ": ", ".join(e["subjects"]),
        })
    return pd.DataFrame(rows)


def _trending_news_to_dataframe(news_items: list[dict]) -> pd.DataFrame:
    """トレンドニュースリストをDataFrameに変換する."""
    if not news_items:
        return pd.DataFrame()
    rows = []
    for rank, item in enumerate(news_items, 1):
        rows.append({
            "順位": rank,
            "タイトル": item["title"],
            "URL": item["url"],
            "関連キーワード": item["keyword"],
            "検索ボリューム": item["traffic"],
            "ソース": item["source"],
        })
    return pd.DataFrame(rows)
