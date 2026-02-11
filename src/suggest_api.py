"""Googleサジェスト非公式APIクライアント."""

from __future__ import annotations

import time
import urllib.parse

import requests
import streamlit as st

SUGGEST_URL = "https://suggestqueries.google.com/complete/search"

# 50音（あ〜ん）
HIRAGANA = [chr(c) for c in range(0x3042, 0x3094)]  # あ〜ゔ (基本50音)
# 実用的な46文字に絞る
HIRAGANA_CHARS = list("あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん")
ALPHABET = [chr(c) for c in range(ord("a"), ord("z") + 1)]
DIGITS = [str(d) for d in range(10)]
ALL_SUFFIXES = HIRAGANA_CHARS + ALPHABET + DIGITS


def fetch_suggestions(query: str) -> list[str]:
    """単一クエリのサジェストを取得する."""
    params = {
        "client": "firefox",
        "ds": "yt",
        "q": query,
    }
    try:
        resp = requests.get(
            SUGGEST_URL,
            params=params,
            timeout=5,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) >= 2:
            return data[1]
    except (requests.RequestException, ValueError):
        pass
    return []


def fetch_suggestions_with_alphabet_soup(
    base_query: str,
    suffixes: list[str] | None = None,
    delay: float = 1.5,
    progress_callback=None,
) -> dict[str, list[str]]:
    """アルファベットスープ法で網羅的にサジェストを取得する.

    Args:
        base_query: ベースとなる検索キーワード
        suffixes: 付加するサフィックスリスト（デフォルト: 50音+英字+数字）
        delay: リクエスト間隔（秒）
        progress_callback: 進捗コールバック(current, total)

    Returns:
        {suffix: [suggestions]} の辞書
    """
    if suffixes is None:
        suffixes = ALL_SUFFIXES

    results: dict[str, list[str]] = {}
    total = len(suffixes)

    for i, suffix in enumerate(suffixes):
        q = f"{base_query} {suffix}"
        results[suffix] = fetch_suggestions(q)
        if progress_callback:
            progress_callback(i + 1, total)
        if i < total - 1:
            time.sleep(delay)

    return results


def flatten_unique_suggestions(
    base_suggestions: list[str],
    soup_results: dict[str, list[str]],
) -> list[str]:
    """全サジェスト結果を統合・重複排除する."""
    seen: set[str] = set()
    unique: list[str] = []

    for s in base_suggestions:
        lower = s.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(s)

    for suggestions in soup_results.values():
        for s in suggestions:
            lower = s.lower()
            if lower not in seen:
                seen.add(lower)
                unique.append(s)

    return unique
