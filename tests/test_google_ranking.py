"""Google検索ワードランキング関連のテスト."""

from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

from src.trends_api import (
    get_category_related_queries,
    get_category_related_topics,
)


# ─── get_category_related_queries ────────────────────


class TestGetCategoryRelatedQueries:
    @patch("src.trends_api.TrendReq")
    def test_success(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.return_value = {
            "": {
                "rising": pd.DataFrame({"query": ["a", "b"], "value": [200, 100]}),
                "top": pd.DataFrame({"query": ["c", "d"], "value": [90, 80]}),
            }
        }
        mock_trend_req.return_value = mock_instance

        result = get_category_related_queries(cat=0, timeframe="today 12-m")
        assert "rising" in result
        assert "top" in result
        assert not result["rising"].empty
        assert not result["top"].empty

        mock_instance.build_payload.assert_called_once_with(
            kw_list=[""], cat=0, timeframe="today 12-m", geo="JP",
        )

    @patch("src.trends_api.TrendReq")
    def test_empty(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.return_value = {
            "": {"rising": None, "top": None}
        }
        mock_trend_req.return_value = mock_instance

        result = get_category_related_queries(cat=3)
        assert isinstance(result["rising"], pd.DataFrame)
        assert result["rising"].empty
        assert isinstance(result["top"], pd.DataFrame)
        assert result["top"].empty

    @patch("src.trends_api.TrendReq")
    def test_error(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.side_effect = Exception("API error")
        mock_trend_req.return_value = mock_instance

        with pytest.raises(Exception, match="API error"):
            get_category_related_queries(cat=5)

    @patch("src.trends_api.TrendReq")
    def test_category_param_passed(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_queries.return_value = {
            "": {
                "rising": pd.DataFrame({"query": ["x"], "value": [50]}),
                "top": pd.DataFrame(),
            }
        }
        mock_trend_req.return_value = mock_instance

        get_category_related_queries(cat=20, timeframe="today 3-m", geo="US")

        mock_instance.build_payload.assert_called_once_with(
            kw_list=[""], cat=20, timeframe="today 3-m", geo="US",
        )


# ─── get_category_related_topics ─────────────────────


class TestGetCategoryRelatedTopics:
    @patch("src.trends_api.TrendReq")
    def test_success(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_topics.return_value = {
            "": {
                "rising": pd.DataFrame({"topic_title": ["Topic A"]}),
                "top": pd.DataFrame({"topic_title": ["Topic B"]}),
            }
        }
        mock_trend_req.return_value = mock_instance

        result = get_category_related_topics(cat=0, timeframe="today 12-m")
        assert not result["rising"].empty
        assert not result["top"].empty

        mock_instance.build_payload.assert_called_once_with(
            kw_list=[""], cat=0, timeframe="today 12-m", geo="JP",
        )

    @patch("src.trends_api.TrendReq")
    def test_keyword_not_found(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_topics.return_value = {}
        mock_trend_req.return_value = mock_instance

        result = get_category_related_topics(cat=7)
        assert result["rising"].empty
        assert result["top"].empty

    @patch("src.trends_api.TrendReq")
    def test_none_values(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_topics.return_value = {
            "": {"rising": None, "top": None}
        }
        mock_trend_req.return_value = mock_instance

        result = get_category_related_topics(cat=16)
        assert isinstance(result["rising"], pd.DataFrame)
        assert isinstance(result["top"], pd.DataFrame)

    @patch("src.trends_api.TrendReq")
    def test_index_error_returns_empty(self, mock_trend_req):
        mock_instance = MagicMock()
        mock_instance.related_topics.side_effect = IndexError("list index out of range")
        mock_trend_req.return_value = mock_instance

        result = get_category_related_topics(cat=0)
        assert result["rising"].empty
        assert result["top"].empty
