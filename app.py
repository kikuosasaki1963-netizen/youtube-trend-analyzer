"""YouTubeトレンド＆競合分析ツール."""

import streamlit as st

from src.constants import DEFAULT_SEARCH_QUERY, PERIOD_OPTIONS
from src.logger import setup_logger
from src.tabs import tab_trending, tab_genre, tab_suggest, tab_buzz, tab_trends, tab_google_ranking
from src.youtube_api import get_quota_tracker

setup_logger()

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
    search_query = st.text_input(
        "検索キーワード",
        value=DEFAULT_SEARCH_QUERY,
        placeholder=f"例: {DEFAULT_SEARCH_QUERY}",
    )

    st.divider()
    st.subheader("フィルタ")

    max_subscribers = st.number_input(
        "登録者数上限", min_value=0, value=0, step=10000, help="0 = 制限なし",
    )
    min_views = st.number_input(
        "再生数下限", min_value=0, value=0, step=1000, help="0 = 制限なし",
    )
    min_vs_ratio = st.number_input(
        "V/S比率下限", min_value=0.0, value=0.0, step=0.1, format="%.1f",
        help="0.0 = 制限なし",
    )

    period_label = st.selectbox("期間", options=list(PERIOD_OPTIONS.keys()))
    period_days = PERIOD_OPTIONS[period_label]

    st.divider()
    st.subheader("クォータ状況")
    tracker = get_quota_tracker()
    st.metric("使用量", f"{tracker.used:,} / {tracker.daily_limit:,}")
    st.progress(min(tracker.usage_percent / 100, 1.0))
    st.caption(f"残り約 {tracker.remaining:,} ユニット")

# ─── メインコンテンツ（タブ） ─────────────────────────
tab_hot, tab_gen, tab_sug, tab_buz, tab_trd, tab_goo = st.tabs(
    ["急上昇トレンド", "ジャンル別ランキング", "サジェストキーワード", "バズ動画分析", "トレンド調査", "Google検索ランキング"]
)

with tab_hot:
    tab_trending.render(api_key)

with tab_gen:
    tab_genre.render(api_key, search_query)

with tab_sug:
    tab_suggest.render(search_query)

with tab_buz:
    tab_buzz.render(api_key, search_query, max_subscribers, min_views, min_vs_ratio, period_days)

with tab_trd:
    tab_trends.render(search_query)

with tab_goo:
    tab_google_ranking.render()
