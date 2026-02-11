"""src/analyzer.py のテスト."""

from src.youtube_api import VideoInfo
from src.analyzer import filter_videos, sort_by_vs_ratio, videos_to_dataframe


def _make_video(
    video_id: str = "v1",
    title: str = "Test",
    view_count: int = 10000,
    subscriber_count: int = 1000,
    vs_ratio: float = 10.0,
) -> VideoInfo:
    return VideoInfo(
        video_id=video_id,
        title=title,
        channel_id="ch1",
        channel_title="TestChannel",
        published_at="2026-01-01T00:00:00Z",
        thumbnail_url="https://example.com/thumb.jpg",
        view_count=view_count,
        subscriber_count=subscriber_count,
        vs_ratio=vs_ratio,
    )


class TestFilterVideos:
    def test_no_filter(self):
        videos = [_make_video()]
        result = filter_videos(videos)
        assert len(result) == 1

    def test_max_subscribers(self):
        videos = [
            _make_video(video_id="v1", subscriber_count=500),
            _make_video(video_id="v2", subscriber_count=5000),
        ]
        result = filter_videos(videos, max_subscribers=1000)
        assert len(result) == 1
        assert result[0].video_id == "v1"

    def test_min_views(self):
        videos = [
            _make_video(video_id="v1", view_count=100),
            _make_video(video_id="v2", view_count=50000),
        ]
        result = filter_videos(videos, min_views=1000)
        assert len(result) == 1
        assert result[0].video_id == "v2"

    def test_min_vs_ratio(self):
        videos = [
            _make_video(video_id="v1", vs_ratio=0.5),
            _make_video(video_id="v2", vs_ratio=5.0),
        ]
        result = filter_videos(videos, min_vs_ratio=1.0)
        assert len(result) == 1
        assert result[0].video_id == "v2"

    def test_combined_filters(self):
        videos = [
            _make_video(video_id="v1", subscriber_count=500, view_count=5000, vs_ratio=10.0),
            _make_video(video_id="v2", subscriber_count=10000, view_count=5000, vs_ratio=0.5),
            _make_video(video_id="v3", subscriber_count=500, view_count=100, vs_ratio=0.2),
        ]
        result = filter_videos(videos, max_subscribers=1000, min_views=1000, min_vs_ratio=1.0)
        assert len(result) == 1
        assert result[0].video_id == "v1"


class TestSortByVsRatio:
    def test_descending(self):
        videos = [
            _make_video(video_id="v1", vs_ratio=1.0),
            _make_video(video_id="v2", vs_ratio=10.0),
            _make_video(video_id="v3", vs_ratio=5.0),
        ]
        result = sort_by_vs_ratio(videos)
        assert [v.video_id for v in result] == ["v2", "v3", "v1"]

    def test_ascending(self):
        videos = [
            _make_video(video_id="v1", vs_ratio=10.0),
            _make_video(video_id="v2", vs_ratio=1.0),
        ]
        result = sort_by_vs_ratio(videos, descending=False)
        assert result[0].video_id == "v2"


class TestVideosToDataframe:
    def test_columns(self):
        videos = [_make_video()]
        df = videos_to_dataframe(videos)
        assert "タイトル" in df.columns
        assert "V/S比率" in df.columns
        assert "動画URL" in df.columns
        assert len(df) == 1

    def test_empty(self):
        df = videos_to_dataframe([])
        assert len(df) == 0
