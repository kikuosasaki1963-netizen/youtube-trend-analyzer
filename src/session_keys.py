"""Streamlit session_state キー定数."""


class SessionKeys:
    """session_state のキー名を一元管理する."""

    QUOTA_TRACKER = "quota_tracker"
    TRENDING_VIDEOS = "trending_videos"
    TRENDING_BY_CATEGORY = "trending_by_category"
    GENRE_VIDEOS = "genre_videos"
    GENRE_LABEL = "genre_label"
    ANALYZED_VIDEOS = "analyzed_videos"
    BASE_SUGGESTIONS = "base_suggestions"
    ALL_SUGGESTIONS = "all_suggestions"
    TRENDING_SEARCHES = "trending_searches"
    TREND_INTEREST = "trend_interest"
    TREND_RELATED = "trend_related"
    TREND_KEYWORD = "trend_keyword"
    GOOGLE_RANKING_QUERIES = "google_ranking_queries"
    GOOGLE_RANKING_TOPICS = "google_ranking_topics"
    GOOGLE_RANKING_CATEGORY = "google_ranking_category"
