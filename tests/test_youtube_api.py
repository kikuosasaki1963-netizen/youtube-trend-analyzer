"""src/youtube_api.py のテスト."""

from src.youtube_api import QuotaTracker, VideoInfo


class TestQuotaTracker:
    def test_initial_state(self):
        tracker = QuotaTracker()
        assert tracker.used == 0
        assert tracker.daily_limit == 10_000
        assert tracker.remaining == 10_000

    def test_add(self):
        tracker = QuotaTracker()
        tracker.add(100)
        assert tracker.used == 100
        assert tracker.remaining == 9_900

    def test_usage_percent(self):
        tracker = QuotaTracker()
        tracker.add(5000)
        assert tracker.usage_percent == 50.0

    def test_remaining_floor(self):
        tracker = QuotaTracker()
        tracker.add(15000)
        assert tracker.remaining == 0


class TestVideoInfo:
    def test_defaults(self):
        v = VideoInfo(
            video_id="v1",
            title="Test",
            channel_id="ch1",
            channel_title="Channel",
            published_at="2026-01-01",
            thumbnail_url="https://example.com/thumb.jpg",
        )
        assert v.view_count == 0
        assert v.subscriber_count == 0
        assert v.vs_ratio == 0.0
