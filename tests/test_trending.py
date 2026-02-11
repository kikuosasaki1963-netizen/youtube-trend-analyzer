"""src/trending.py のテスト."""

import pandas as pd

from src.trending import (
    CATEGORY_MAP,
    flatten_category_videos,
    extract_keywords_from_titles,
    analyze_trending_categories,
    trending_to_dataframe,
)


# ─── ヘルパー ─────────────────────────────────────────

def _make_video(
    video_id: str = "v1",
    title: str = "テスト動画",
    category_id: str = "24",
    view_count: int = 10000,
    like_count: int = 500,
    channel_title: str = "テストチャンネル",
) -> dict:
    return {
        "id": video_id,
        "snippet": {
            "title": title,
            "channelTitle": channel_title,
            "publishedAt": "2026-01-15T12:00:00Z",
            "categoryId": category_id,
            "thumbnails": {
                "high": {"url": "https://example.com/high.jpg"},
            },
        },
        "statistics": {
            "viewCount": str(view_count),
            "likeCount": str(like_count),
        },
    }


# ─── flatten_category_videos ─────────────────────────

class TestFlattenCategoryVideos:
    def test_dedup_across_categories(self):
        category_videos = {
            "音楽": [_make_video("v1"), _make_video("v2")],
            "ゲーム": [_make_video("v2"), _make_video("v3")],
        }
        result = flatten_category_videos(category_videos)
        assert len(result) == 3
        ids = [v["id"] for v in result]
        assert ids == ["v1", "v2", "v3"]

    def test_empty_input(self):
        result = flatten_category_videos({})
        assert result == []

    def test_single_category(self):
        category_videos = {
            "音楽": [_make_video("v1"), _make_video("v2")],
        }
        result = flatten_category_videos(category_videos)
        assert len(result) == 2


# ─── extract_keywords_from_titles ────────────────────

class TestExtractKeywordsFromTitles:
    def test_japanese_keywords(self):
        videos = [
            _make_video(title="不動産投資で年間500万円稼ぐ方法"),
            _make_video(title="不動産投資の初心者ガイド"),
        ]
        result = extract_keywords_from_titles(videos)
        keywords = [kw for kw, _ in result]
        assert "不動産投資" in keywords

    def test_english_keywords(self):
        videos = [
            _make_video(title="Python Tutorial for Beginners"),
            _make_video(title="Python Advanced Tips"),
        ]
        result = extract_keywords_from_titles(videos)
        keywords = [kw for kw, _ in result]
        assert "Python" in keywords

    def test_stopwords_filtered(self):
        videos = [_make_video(title="これはテストです")]
        result = extract_keywords_from_titles(videos)
        keywords = [kw for kw, _ in result]
        # 助詞「は」「です」はストップワード → 含まれない
        assert "は" not in keywords
        assert "です" not in keywords

    def test_top_n_limit(self):
        videos = [
            _make_video(title="キーワードA キーワードB キーワードC キーワードD キーワードE"),
        ]
        result = extract_keywords_from_titles(videos, top_n=3)
        assert len(result) <= 3

    def test_empty_videos(self):
        result = extract_keywords_from_titles([])
        assert result == []


# ─── analyze_trending_categories ─────────────────────

class TestAnalyzeTrendingCategories:
    def test_count_by_category(self):
        videos = [
            _make_video(category_id="10"),  # 音楽
            _make_video(category_id="10"),
            _make_video(category_id="17"),  # スポーツ
        ]
        result = analyze_trending_categories(videos)
        assert isinstance(result, pd.DataFrame)
        music_row = result[result["カテゴリ"] == "音楽"]
        assert music_row["件数"].values[0] == 2

    def test_unknown_category(self):
        videos = [_make_video(category_id="999")]
        result = analyze_trending_categories(videos)
        assert "その他(999)" in result["カテゴリ"].values

    def test_empty_videos(self):
        result = analyze_trending_categories([])
        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ─── trending_to_dataframe ───────────────────────────

class TestTrendingToDataframe:
    def test_columns(self):
        videos = [_make_video()]
        df = trending_to_dataframe(videos)
        expected_cols = {"タイトル", "チャンネル", "再生数", "高評価", "カテゴリ", "公開日", "動画URL"}
        assert expected_cols == set(df.columns)

    def test_empty(self):
        df = trending_to_dataframe([])
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    def test_data_types(self):
        videos = [_make_video(view_count=50000, like_count=1000)]
        df = trending_to_dataframe(videos)
        assert df["再生数"].iloc[0] == 50000
        assert df["高評価"].iloc[0] == 1000
