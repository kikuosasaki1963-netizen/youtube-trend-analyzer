"""src/suggest_api.py のテスト."""

from unittest.mock import patch, MagicMock

from src.suggest_api import (
    fetch_suggestions,
    flatten_unique_suggestions,
    HIRAGANA_CHARS,
    ALPHABET,
    DIGITS,
    ALL_SUFFIXES,
)


class TestFetchSuggestions:
    @patch("src.suggest_api.requests.get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = ["query", ["suggestion1", "suggestion2"]]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = fetch_suggestions("test")
        assert result == ["suggestion1", "suggestion2"]

    @patch("src.suggest_api.requests.get")
    def test_empty_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = ["query", []]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = fetch_suggestions("test")
        assert result == []

    @patch("src.suggest_api.requests.get")
    def test_network_error(self, mock_get):
        import requests

        mock_get.side_effect = requests.RequestException("timeout")
        result = fetch_suggestions("test")
        assert result == []


class TestFlattenUniqueSuggestions:
    def test_dedup(self):
        base = ["A", "B", "C"]
        soup = {"あ": ["B", "D"], "い": ["C", "E"]}
        result = flatten_unique_suggestions(base, soup)
        assert result == ["A", "B", "C", "D", "E"]

    def test_case_insensitive(self):
        base = ["Hello"]
        soup = {"a": ["hello", "HELLO", "World"]}
        result = flatten_unique_suggestions(base, soup)
        assert len(result) == 2
        assert result[0] == "Hello"
        assert result[1] == "World"

    def test_empty(self):
        result = flatten_unique_suggestions([], {})
        assert result == []


class TestConstants:
    def test_hiragana_count(self):
        assert len(HIRAGANA_CHARS) == 46

    def test_alphabet_count(self):
        assert len(ALPHABET) == 26

    def test_digits_count(self):
        assert len(DIGITS) == 10

    def test_all_suffixes_count(self):
        assert len(ALL_SUFFIXES) == 82
