"""ジャンル別ランキングタブ."""

from __future__ import annotations

from src.session_keys import SessionKeys

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.constants import GENRE_PERIOD_OPTIONS
from src.trending import (
    CATEGORY_MAP,
    fetch_trending_videos,
    extract_keywords_from_titles,
)
from src.ui_components import (
    csv_download_button,
    display_video_grid_raw,
    extract_thumbnail_url,
)
from src.youtube_api import (
    QuotaExceededError,
    get_quota_tracker,
    get_video_details,
    get_youtube_client,
)
from src.utils import format_number


def render(api_key: str, search_query: str) -> None:
    """ジャンル別ランキングタブを描画する."""
    st.subheader("ジャンル別 人気キーワードランキング")
    st.caption(
        "指定ジャンル・期間で再生数の多い動画からバズキーワードを抽出します。"
        "キーワード検索: 102ユニット / キーワードなし: 1ユニット"
    )

    _genre_map: dict[str, str] = {"全ジャンル": "0"}
    _genre_map.update({v: k for k, v in CATEGORY_MAP.items()})

    genre_col1, genre_col2 = st.columns(2)
    with genre_col1:
        selected_genre = st.selectbox(
            "ジャンル", options=list(_genre_map.keys()), key="genre_select",
        )
    with genre_col2:
        selected_period = st.selectbox(
            "期間", options=list(GENRE_PERIOD_OPTIONS.keys()), key="genre_period",
        )

    genre_keyword = st.text_input(
        "検索キーワード（任意）",
        value=search_query,
        key="genre_keyword",
        help="空欄の場合はジャンル全体のランキングを取得します",
    )

    if st.button("ランキング取得", type="primary", use_container_width=True, key="genre_btn"):
        days = GENRE_PERIOD_OPTIONS[selected_period]
        category_id = _genre_map[selected_genre]
        has_keyword = bool(genre_keyword.strip())
        tracker = get_quota_tracker()

        try:
            if has_keyword:
                genre_videos = _fetch_with_keyword(
                    api_key, genre_keyword.strip(), category_id, days, tracker,
                )
            else:
                genre_videos = _fetch_without_keyword(api_key, category_id)

            genre_videos.sort(key=lambda x: x["view_count"], reverse=True)
            st.session_state[SessionKeys.GENRE_VIDEOS] = genre_videos
            st.session_state[SessionKeys.GENRE_LABEL] = f"{selected_genre}（{selected_period}）"

            if not genre_videos:
                st.warning("該当する動画が見つかりませんでした。条件を変えてお試しください。")

        except QuotaExceededError:
            st.warning("APIクォータを超過しました。")
        except Exception as e:
            st.error(f"エラーが発生しました: {type(e).__name__}: {e}")

    _display_results(search_query)


def _fetch_with_keyword(
    api_key: str,
    keyword: str,
    category_id: str,
    days: int,
    tracker,
) -> list[dict]:
    """キーワード検索でジャンル別動画を取得する."""
    with st.spinner(f"「{keyword}」を検索中..."):
        dt = datetime.utcnow() - timedelta(days=days)
        published_after = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        youtube = get_youtube_client(api_key)

        params = {
            "part": "snippet",
            "type": "video",
            "q": keyword,
            "maxResults": 50,
            "order": "viewCount",
            "regionCode": "JP",
            "publishedAfter": published_after,
        }
        if category_id != "0":
            params["videoCategoryId"] = category_id

        response = youtube.search().list(**params).execute()
        tracker.add(100)
        items = response.get("items", [])

        video_ids = tuple(
            item["id"]["videoId"]
            for item in items
            if item.get("id", {}).get("videoId")
        )
        video_stats = get_video_details(api_key, video_ids) if video_ids else {}

        genre_videos = []
        for item in items:
            vid = item.get("id", {}).get("videoId", "")
            if not vid:
                continue
            snippet = item["snippet"]
            stats = video_stats.get(vid, {})
            genre_videos.append({
                "id": vid,
                "snippet": snippet,
                "statistics": stats,
                "thumbnail_url": extract_thumbnail_url(snippet),
                "view_count": int(stats.get("viewCount", 0)),
            })

    return genre_videos


def _fetch_without_keyword(api_key: str, category_id: str) -> list[dict]:
    """キーワードなしでジャンル別人気動画を取得する."""
    with st.spinner("人気動画を取得中..."):
        if category_id == "0":
            all_items = []
            for cat_id in CATEGORY_MAP:
                vids = fetch_trending_videos(
                    api_key, category_id=cat_id, max_results=50,
                )
                all_items.extend(vids)
        else:
            all_items = fetch_trending_videos(
                api_key, category_id=category_id, max_results=50,
            )

        genre_videos = []
        seen_ids: set[str] = set()
        for v in all_items:
            vid = v.get("id", "")
            if vid in seen_ids:
                continue
            seen_ids.add(vid)
            snippet = v.get("snippet", {})
            stats = v.get("statistics", {})
            genre_videos.append({
                "id": vid,
                "snippet": snippet,
                "statistics": stats,
                "thumbnail_url": extract_thumbnail_url(snippet),
                "view_count": int(stats.get("viewCount", 0)),
            })

    return genre_videos


def _display_results(search_query: str) -> None:
    """ジャンル別ランキングの結果を表示する."""
    if SessionKeys.GENRE_VIDEOS not in st.session_state or not st.session_state[SessionKeys.GENRE_VIDEOS]:
        return

    genre_videos = st.session_state[SessionKeys.GENRE_VIDEOS]
    label = st.session_state.get(SessionKeys.GENRE_LABEL, "")
    st.success(f"「{label}」: {len(genre_videos)} 件の動画を取得")

    # キーワードランキング
    st.markdown(f"### バズキーワード ランキング - {label}")
    keywords = extract_keywords_from_titles(genre_videos)
    if keywords:
        kw_df = pd.DataFrame(keywords, columns=["キーワード", "出現回数"])
        col_chart, col_table = st.columns([2, 1])
        with col_chart:
            st.bar_chart(kw_df.set_index("キーワード"), horizontal=True, height=600)
        with col_table:
            st.dataframe(kw_df, use_container_width=True, height=600)

    # 動画サムネイル一覧
    st.markdown(f"### 人気動画 TOP15 - {label}")
    display_video_grid_raw(genre_videos)

    # CSVダウンロード
    st.divider()
    rows = []
    for v in genre_videos:
        snippet = v.get("snippet", {})
        rows.append({
            "タイトル": snippet.get("title", ""),
            "チャンネル": snippet.get("channelTitle", ""),
            "再生数": v["view_count"],
            "公開日": snippet.get("publishedAt", "")[:10],
            "動画URL": f"https://www.youtube.com/watch?v={v['id']}",
        })
    df_genre = pd.DataFrame(rows)
    st.dataframe(df_genre, use_container_width=True, height=400)
    csv_download_button(df_genre, f"genre_ranking.csv", "genre_csv")
