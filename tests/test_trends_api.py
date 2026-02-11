"""src/trends_api.py のテスト."""

from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.trends_api import (
    get_trending_searches,
    get_interest_over_time,
    get_related_queries,
    get_related_topics,
)


# ─── ヘルパー ─────────────────────────────────────────

SAMPLE_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss">
  <channel>
    <item>
      <title>TestKeyword</title>
      <ht:approx_traffic>500,000+</ht:approx_traffic>
      <ht:picture>https://example.com/pic.jpg</ht:picture>
      <ht:news_item>
        <ht:news_item_title>TestNews</ht:news_item_title>
        <ht:news_item_source>TestSource</ht:news_item_source>
        <ht:news_item_url>https://example.com/news</ht:news_item_url>
      </ht:news_item>
    </item>
  </channel>
</rss>
""".encode("utf-8")

EMPTY_RSS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss">
  <channel></channel>
</rss>
""".encode("utf-8")


# ─── get_trending_searches ───────────────────────────

class TestGetTrendingSearches:
    @patch("src.trends_api.requests.get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = SAMPLE_RSS_XML
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = get_trending_searches("JP")
        assert len(result) == 1
        assert result[0]["keyword"] == "TestKeyword"
        assert result[0]["traffic"] == "500,000+"
        assert len(result[0]["news"]) == 1
        assert result[0]["news"][0]["title"] == "TestNews"

    @patch("src.trends_api.requests.get")
    def test_empty_result(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = EMPTY_RSS_XML
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = get_trending_searches("JP")
        assert result == []

    @patch("src.trends_api.requests.get")
    def test_network_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError("timeout")

        with pytest.raises(requests.ConnectionError):
            get_trending_searches("JP")

    @patch("src.trends_api.requests.get")
    def test_http_error(self, mock_get):
        import requests
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = requests.HTTPError("500")
        mock_get.return_value = mock_resp

        with pytest.raises(requests.HTTPError):
            get_trending_searches("JP")


# ─── get_interest_over_time ──────────────────────────

class TestGetInterestOverTime:
    @patch("src.trends_api.TrendReq")
    def test_returns_dataframe(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.interest_over_time.return_value = pd.DataFrame({
            "テスト": [50, 60, 70],
            "isPartial": [False, False, True],
        })
        mock_trend_req.return_value = mock_instance

        result = get_interest_over_time("テスト")
        assert isinstance(result, pd.DataFrame)
        assert "テスト" in result.columns
        assert "isPartial" not in result.columns

    @patch("src.trends_api.TrendReq")
    def test_empty_dataframe(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.interest_over_time.return_value = pd.DataFrame()
        mock_trend_req.return_value = mock_instance

        result = get_interest_over_time("存在しないキーワード")
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    @patch("src.trends_api.TrendReq")
    def test_pytrends_exception(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.interest_over_time.side_effect = Exception("pytrends error")
        mock_trend_req.return_value = mock_instance

        with pytest.raises(Exception, match="pytrends error"):
            get_interest_over_time("テスト")


# ─── get_related_queries ─────────────────────────────

class TestGetRelatedQueries:
    @patch("src.trends_api.TrendReq")
    def test_returns_rising_and_top(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.return_value = {
            "テスト": {
                "rising": pd.DataFrame({"query": ["a"], "value": [100]}),
                "top": pd.DataFrame({"query": ["b"], "value": [80]}),
            }
        }
        mock_trend_req.return_value = mock_instance

        result = get_related_queries("テスト")
        assert "rising" in result
        assert "top" in result
        assert not result["rising"].empty
        assert not result["top"].empty

    @patch("src.trends_api.TrendReq")
    def test_keyword_not_found(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.return_value = {}
        mock_trend_req.return_value = mock_instance

        result = get_related_queries("存在しないキーワード")
        assert result["rising"].empty
        assert result["top"].empty

    @patch("src.trends_api.TrendReq")
    def test_none_values(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.return_value = {
            "テスト": {"rising": None, "top": None}
        }
        mock_trend_req.return_value = mock_instance

        result = get_related_queries("テスト")
        assert isinstance(result["rising"], pd.DataFrame)
        assert isinstance(result["top"], pd.DataFrame)


# ─── get_related_topics ──────────────────────────────

class TestGetRelatedTopics:
    @patch("src.trends_api.TrendReq")
    def test_returns_rising_and_top(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_topics.return_value = {
            "テスト": {
                "rising": pd.DataFrame({"topic_title": ["x"]}),
                "top": pd.DataFrame({"topic_title": ["y"]}),
            }
        }
        mock_trend_req.return_value = mock_instance

        result = get_related_topics("テスト")
        assert not result["rising"].empty
        assert not result["top"].empty

    @patch("src.trends_api.TrendReq")
    def test_keyword_not_found(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_topics.return_value = {}
        mock_trend_req.return_value = mock_instance

        result = get_related_topics("存在しないキーワード")
        assert result["rising"].empty
        assert result["top"].empty
