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
from src.trends_api import (
    get_trending_searches,
    get_interest_over_time,
    get_related_queries,
)
from src.trending import (
    CATEGORY_MAP,
    fetch_trending_videos,
    fetch_trending_all_categories,
    flatten_category_videos,
    extract_keywords_from_titles,
    analyze_trending_categories,
    trending_to_dataframe,
)
from src.utils import format_number, video_url
from src.youtube_api import (
    QuotaExceededError,
    get_quota_tracker,
    get_youtube_client,
    get_video_details,
)

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
tab_hot, tab_genre, tab_suggest, tab_buzz, tab_trends = st.tabs(["急上昇トレンド", "ジャンル別ランキング", "サジェストキーワード", "バズ動画分析", "トレンド調査"])

# ─── タブ0: 急上昇トレンド ────────────────────────────
with tab_hot:
    st.subheader("YouTube 急上昇トレンド（日本）")
    st.caption("今YouTube日本で何がバズっているかを一目で把握できます。クォータ消費: 1ユニット/回")

    if st.button("急上昇データ取得（全カテゴリ）", type="primary", use_container_width=True):
        try:
            with st.spinner("全カテゴリの急上昇動画を取得中（約15ユニット消費）..."):
                category_videos = fetch_trending_all_categories(api_key)
                all_videos = flatten_category_videos(category_videos)

            st.session_state["trending_videos"] = all_videos
            st.session_state["trending_by_category"] = category_videos
        except QuotaExceededError:
            st.warning("APIクォータを超過しました。")

    if "trending_videos" in st.session_state and st.session_state["trending_videos"]:
        trending_videos = st.session_state["trending_videos"]
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
        cols_per_row = 3
        for i in range(0, min(len(trending_videos), 15), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(trending_videos):
                    break
                v = trending_videos[idx]
                snippet = v.get("snippet", {})
                stats = v.get("statistics", {})
                thumbnails = snippet.get("thumbnails", {})
                thumb_url = (
                    thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url")
                    or thumbnails.get("default", {}).get("url", "")
                )
                with col:
                    with st.container(border=True):
                        st.image(thumb_url, use_container_width=True)
                        vid_url = f"https://www.youtube.com/watch?v={v['id']}"
                        st.markdown(f"**[{snippet.get('title', '')}]({vid_url})**")
                        st.caption(f"{snippet.get('channelTitle', '')} / {format_number(int(stats.get('viewCount', 0)))}回再生")

        # データテーブル＆CSVダウンロード
        st.divider()
        df_trending = trending_to_dataframe(trending_videos)
        st.dataframe(df_trending, use_container_width=True, height=400)

        csv_trending = df_trending.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "CSVダウンロード",
            csv_trending,
            file_name="youtube_trending_jp.csv",
            mime="text/csv",
            key="trending_csv",
        )

# ─── タブ: ジャンル別ランキング ──────────────────────
with tab_genre:
    st.subheader("ジャンル別 人気キーワードランキング")
    st.caption("指定ジャンル・期間で再生数の多い動画からバズキーワードを抽出します。キーワード検索: 102ユニット / キーワードなし: 1ユニット")

    _genre_map = {"全ジャンル": "0"}
    _genre_map.update({v: k for k, v in CATEGORY_MAP.items()})

    genre_col1, genre_col2 = st.columns(2)
    with genre_col1:
        selected_genre = st.selectbox(
            "ジャンル", options=list(_genre_map.keys()), key="genre_select",
        )
    with genre_col2:
        genre_period_options = {
            "過去7日": 7,
            "過去30日": 30,
            "過去90日": 90,
            "過去1年": 365,
        }
        selected_period = st.selectbox(
            "期間", options=list(genre_period_options.keys()), key="genre_period",
        )

    genre_keyword = st.text_input(
        "検索キーワード（任意）",
        value=search_query,
        key="genre_keyword",
        help="空欄の場合はジャンル全体のランキングを取得します",
    )

    if st.button("ランキング取得", type="primary", use_container_width=True, key="genre_btn"):
        days = genre_period_options[selected_period]
        category_id = _genre_map[selected_genre]
        has_keyword = bool(genre_keyword.strip())

        try:
            if has_keyword:
                # キーワードあり → search.list（100ユニット）
                with st.spinner(f"「{genre_keyword.strip()}」× {selected_genre} を検索中..."):
                    dt = datetime.utcnow() - timedelta(days=days)
                    published_after = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    youtube = get_youtube_client(api_key)

                    params = {
                        "part": "snippet",
                        "type": "video",
                        "q": genre_keyword.strip(),
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

                    # video details で再生数取得
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
                        thumbnails = snippet.get("thumbnails", {})
                        thumb_url = (
                            thumbnails.get("high", {}).get("url")
                            or thumbnails.get("medium", {}).get("url")
                            or thumbnails.get("default", {}).get("url", "")
                        )
                        genre_videos.append({
                            "id": vid,
                            "snippet": snippet,
                            "statistics": stats,
                            "thumbnail_url": thumb_url,
                            "view_count": int(stats.get("viewCount", 0)),
                        })
            else:
                # キーワードなし → videos.list mostPopular（1ユニット/カテゴリ）
                with st.spinner(f"「{selected_genre}」の人気動画を取得中..."):
                    if category_id == "0":
                        # 全ジャンル: カテゴリごとに取得
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
                    seen_ids = set()
                    for v in all_items:
                        vid = v.get("id", "")
                        if vid in seen_ids:
                            continue
                        seen_ids.add(vid)
                        snippet = v.get("snippet", {})
                        stats = v.get("statistics", {})
                        thumbnails = snippet.get("thumbnails", {})
                        thumb_url = (
                            thumbnails.get("high", {}).get("url")
                            or thumbnails.get("medium", {}).get("url")
                            or thumbnails.get("default", {}).get("url", "")
                        )
                        genre_videos.append({
                            "id": vid,
                            "snippet": snippet,
                            "statistics": stats,
                            "thumbnail_url": thumb_url,
                            "view_count": int(stats.get("viewCount", 0)),
                        })

            genre_videos.sort(key=lambda x: x["view_count"], reverse=True)
            st.session_state["genre_videos"] = genre_videos
            st.session_state["genre_label"] = f"{selected_genre}（{selected_period}）"

            if not genre_videos:
                st.warning("該当する動画が見つかりませんでした。条件を変えてお試しください。")

        except QuotaExceededError:
            st.warning("APIクォータを超過しました。")
        except Exception as e:
            st.error(f"エラーが発生しました: {type(e).__name__}: {e}")

    if "genre_videos" in st.session_state and st.session_state["genre_videos"]:
        genre_videos = st.session_state["genre_videos"]
        label = st.session_state.get("genre_label", "")
        st.success(f"「{label}」: {len(genre_videos)} 件の動画を取得")

        # キーワードランキング
        st.markdown(f"### バズキーワード ランキング - {label}")
        # snippet構造を持つのでそのまま使える
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
        cols_per_row = 3
        for i in range(0, min(len(genre_videos), 15), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(genre_videos):
                    break
                v = genre_videos[idx]
                snippet = v.get("snippet", {})
                with col:
                    with st.container(border=True):
                        st.image(v["thumbnail_url"], use_container_width=True)
                        vid_url = f"https://www.youtube.com/watch?v={v['id']}"
                        st.markdown(f"**[{snippet.get('title', '')}]({vid_url})**")
                        st.caption(
                            f"{snippet.get('channelTitle', '')} / "
                            f"{format_number(v['view_count'])}回再生"
                        )

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

        csv_genre = df_genre.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "CSVダウンロード",
            csv_genre,
            file_name=f"genre_ranking_{selected_genre}.csv",
            mime="text/csv",
            key="genre_csv",
        )

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

# ─── タブ3: トレンド調査 ─────────────────────────────
with tab_trends:
    st.subheader("トレンド調査")
    st.caption("Google Trends のデータから、今注目されている検索キーワードを確認できます。APIクォータ消費なし。")

    # ── セクション1: 今日の急上昇ワード（キーワード不要） ──
    st.markdown("### 急上昇検索ワード（日本・過去7日間）")
    st.caption("Google検索で直近7日間に急上昇したキーワード一覧。キーワード指定不要で取得できます。")

    if st.button("急上昇ワードを取得", use_container_width=True, key="trending_searches_btn"):
        try:
            with st.spinner("Google Trends 急上昇ワードを取得中..."):
                trending_df = get_trending_searches(geo="JP")
            st.session_state["trending_searches"] = trending_df
        except Exception as e:
            st.error(f"取得に失敗しました: {e}")

    if "trending_searches" in st.session_state:
        trending_df = st.session_state["trending_searches"]
        if not trending_df.empty:
            st.success(f"{len(trending_df)} 件の急上昇ワードを取得")
            st.dataframe(trending_df, use_container_width=True, height=500)

            csv_trending_kw = trending_df.to_csv().encode("utf-8-sig")
            st.download_button(
                "CSVダウンロード",
                csv_trending_kw,
                file_name="google_trending_searches_jp.csv",
                mime="text/csv",
                key="trending_searches_csv",
            )
        else:
            st.info("急上昇ワードが取得できませんでした。")

    # ── セクション2: キーワード別の検索ボリューム調査 ──
    st.divider()
    st.markdown("### キーワード別 検索ボリューム調査")
    st.caption("特定キーワードの検索ボリューム推移と関連キーワードを表示します。")

    trend_period = st.selectbox(
        "調査期間",
        options=["過去12ヶ月", "過去3ヶ月", "過去1ヶ月", "過去7日"],
        key="trend_period",
    )
    period_map = {
        "過去12ヶ月": "today 12-m",
        "過去3ヶ月": "today 3-m",
        "過去1ヶ月": "today 1-m",
        "過去7日": "now 7-d",
    }

    if st.button("トレンド調査開始", type="primary", use_container_width=True):
        if not search_query:
            st.warning("サイドバーで検索キーワードを入力してください。")
        else:
            try:
                with st.spinner("Google Trends データ取得中..."):
                    timeframe = period_map[trend_period]
                    interest_df = get_interest_over_time(search_query, timeframe=timeframe)
                    related = get_related_queries(search_query)

                st.session_state["trend_interest"] = interest_df
                st.session_state["trend_related"] = related
                st.session_state["trend_keyword"] = search_query

            except Exception as e:
                st.error(f"データ取得に失敗しました: {e}")

    if "trend_interest" in st.session_state and st.session_state.get("trend_keyword"):
        kw = st.session_state["trend_keyword"]
        interest_df = st.session_state["trend_interest"]
        related = st.session_state["trend_related"]

        # 検索ボリューム推移グラフ
        st.markdown(f"### 「{kw}」の検索ボリューム推移")
        if not interest_df.empty:
            st.line_chart(interest_df[kw], use_container_width=True, height=300)
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
