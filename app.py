"""YouTubeトレンド＆競合分析ツール."""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from src.analyzer import (
    fetch_and_analyze,
    filter_videos,
    sort_by_vs_ratio,
    videos_to_dataframe,
)
from src.suggest_api import (
    fetch_suggestions,
    fetch_suggestions_with_alphabet_soup,
    flatten_unique_suggestions,
)
from src.utils import format_number, video_url
from src.youtube_api import QuotaExceededError, get_quota_tracker

# ─── ページ設定 ───────────────────────────────────────
st.set_page_config(
    page_title="YouTube トレンド分析",
    page_icon="🔍",
    layout="wide",
)

st.title("YouTube トレンド＆競合分析ツール")

# ─── APIキーチェック ──────────────────────────────────
try:
    api_key = st.secrets["YOUTUBE_API_KEY"]
except (KeyError, FileNotFoundError):
    api_key = ""

if not api_key:
    st.error(
        "YouTube API キーが未設定です。\n\n"
        "**ローカル環境の場合:**\n"
        "`.streamlit/secrets.toml` に以下を追加:\n"
        '```\nYOUTUBE_API_KEY = "YOUR_API_KEY"\n```\n\n'
        "**Streamlit Community Cloud の場合:**\n"
        "アプリ設定 → Secrets に上記と同じ内容を入力\n\n"
        "**APIキー取得手順:**\n"
        "1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成\n"
        "2. YouTube Data API v3 を有効化\n"
        "3. APIキーを作成"
    )
    st.stop()

# ─── サイドバー ──────────────────────────────────────
with st.sidebar:
    st.header("検索設定")
    search_query = st.text_input("検索キーワード", value="不動産投資", placeholder="例: 不動産投資")

    st.divider()
    st.subheader("フィルタ")

    max_subscribers = st.number_input(
        "登録者数上限",
        min_value=0,
        value=0,
        step=10000,
        help="0 = 制限なし",
    )

    min_views = st.number_input(
        "再生数下限",
        min_value=0,
        value=0,
        step=1000,
        help="0 = 制限なし",
    )

    min_vs_ratio = st.number_input(
        "V/S比率下限",
        min_value=0.0,
        value=0.0,
        step=0.1,
        format="%.1f",
        help="0.0 = 制限なし",
    )

    period_options = {
        "制限なし": None,
        "過去7日": 7,
        "過去30日": 30,
        "過去90日": 90,
        "過去1年": 365,
    }
    period_label = st.selectbox("期間", options=list(period_options.keys()))
    period_days = period_options[period_label]

    st.divider()
    st.subheader("クォータ状況")
    tracker = get_quota_tracker()
    st.metric("使用量", f"{tracker.used:,} / {tracker.daily_limit:,}")
    st.progress(min(tracker.usage_percent / 100, 1.0))
    st.caption(f"残り約 {tracker.remaining:,} ユニット")

# ─── メインコンテンツ（タブ） ─────────────────────────
tab_suggest, tab_buzz = st.tabs(["サジェストキーワード", "バズ動画分析"])

# ─── タブ1: サジェストキーワード ──────────────────────
with tab_suggest:
    st.subheader("サジェストキーワード収集")
    st.caption("Googleサジェスト非公式APIを使って、関連キーワードを網羅的に取得します。")

    col_base, col_soup = st.columns(2)

    with col_base:
        if st.button("基本サジェスト取得", use_container_width=True):
            if not search_query:
                st.warning("検索キーワードを入力してください。")
            else:
                with st.spinner("サジェスト取得中..."):
                    suggestions = fetch_suggestions(search_query)
                st.session_state["base_suggestions"] = suggestions

    with col_soup:
        if st.button("アルファベットスープ取得（約2分）", use_container_width=True):
            if not search_query:
                st.warning("検索キーワードを入力してください。")
            else:
                progress_bar = st.progress(0, text="サジェスト収集中...")

                def update_progress(current: int, total: int):
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

                base = st.session_state.get("base_suggestions", [])
                if not base:
                    base = fetch_suggestions(search_query)
                    st.session_state["base_suggestions"] = base

                all_keywords = flatten_unique_suggestions(base, soup_results)
                st.session_state["all_suggestions"] = all_keywords

    # 結果表示
    if "all_suggestions" in st.session_state and st.session_state["all_suggestions"]:
        keywords = st.session_state["all_suggestions"]
        st.success(f"{len(keywords)} 件のユニークキーワードを取得しました")

        df_kw = pd.DataFrame({"キーワード": keywords})
        st.dataframe(df_kw, use_container_width=True, height=400)

        csv_kw = df_kw.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "CSVダウンロード",
            csv_kw,
            file_name=f"suggestions_{search_query}.csv",
            mime="text/csv",
        )

    elif "base_suggestions" in st.session_state and st.session_state["base_suggestions"]:
        suggestions = st.session_state["base_suggestions"]
        st.info(f"{len(suggestions)} 件の基本サジェストを取得しました")

        df_base = pd.DataFrame({"キーワード": suggestions})
        st.dataframe(df_base, use_container_width=True)

# ─── タブ2: バズ動画分析 ─────────────────────────────
with tab_buzz:
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

                # フィルタ適用
                filtered = filter_videos(
                    videos,
                    max_subscribers=max_subscribers if max_subscribers > 0 else None,
                    min_views=min_views if min_views > 0 else None,
                    min_vs_ratio=min_vs_ratio if min_vs_ratio > 0 else None,
                )

                # V/S比率でソート
                sorted_videos = sort_by_vs_ratio(filtered)
                st.session_state["analyzed_videos"] = sorted_videos

            except QuotaExceededError:
                st.warning(
                    "APIクォータを超過しました。"
                    "クォータは太平洋時間の午前0時（日本時間16:00）にリセットされます。"
                )

    # 結果表示
    if "analyzed_videos" in st.session_state and st.session_state["analyzed_videos"]:
        sorted_videos = st.session_state["analyzed_videos"]
        st.success(f"{len(sorted_videos)} 件の動画が見つかりました")

        # サムネイルグリッド表示
        cols_per_row = 3
        for i in range(0, len(sorted_videos), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(sorted_videos):
                    break
                v = sorted_videos[idx]
                with col:
                    with st.container(border=True):
                        st.image(v.thumbnail_url, use_container_width=True)
                        st.markdown(
                            f"**[{v.title}]({video_url(v.video_id)})**"
                        )
                        metric_cols = st.columns(3)
                        metric_cols[0].metric("V/S比率", f"{v.vs_ratio:.1f}")
                        metric_cols[1].metric("再生数", format_number(v.view_count))
                        metric_cols[2].metric("登録者", format_number(v.subscriber_count))

        # データテーブル＆CSVダウンロード
        st.divider()
        df = videos_to_dataframe(sorted_videos)
        st.dataframe(df, use_container_width=True, height=400)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "CSVダウンロード",
            csv,
            file_name=f"buzz_videos_{search_query}.csv",
            mime="text/csv",
        )

    elif "analyzed_videos" in st.session_state:
        st.info("条件に一致する動画が見つかりませんでした。フィルタ条件を緩めてお試しください。")
