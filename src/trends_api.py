"""Google Trends APIクライアント（pytrends + RSS）."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from pytrends.exceptions import TooManyRequestsError
from pytrends.request import TrendReq
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger("youtube_analyzer")


class TrendsRateLimitError(Exception):
    """Google Trends からレート制限（HTTP 429）を受けた場合に送出される."""


def _build_pytrends() -> TrendReq:
    """pytrendsクライアントを構築する.

    retries/backoff_factorは渡さない（pytrendsが内部でurllib3.Retryに
    `method_whitelist`を渡すが、urllib3 v2.xで削除されTypeErrorになるため）。
    リトライは外側のtenacityデコレータで実装している。
    """
    return TrendReq(
        hl="ja-JP",
        tz=540,
        timeout=(10, 25),
    )


_RATE_LIMIT_EXCEPTIONS = (TooManyRequestsError, requests.HTTPError)


def _is_rate_limit(exc: BaseException) -> bool:
    if isinstance(exc, TooManyRequestsError):
        return True
    if isinstance(exc, requests.HTTPError):
        resp = getattr(exc, "response", None)
        return resp is not None and resp.status_code == 429
    return False


_retry_pytrends = retry(
    retry=retry_if_exception_type(_RATE_LIMIT_EXCEPTIONS),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=5, max=60),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


def get_trending_searches(geo: str = "JP") -> list[dict]:
    """急上昇キーワードを取得する（Google Trends RSSから）.

    Args:
        geo: 地域コード（"JP", "US" 等）

    Returns:
        [{"keyword": str, "traffic": str, "news": [...]}]

    Raises:
        requests.RequestException: ネットワークエラー時
    """
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        logger.warning("Google Trends RSS: XML解析に失敗しました")
        return []

    ns = {"ht": "https://trends.google.com/trending/rss"}

    results = []
    for item in root.iter("item"):
        keyword = item.findtext("title", "")
        traffic = item.findtext("ht:approx_traffic", "", ns)
        picture = item.findtext("ht:picture", "", ns)
        if not keyword:
            continue

        news_items = []
        for ni in item.findall("ht:news_item", ns):
            news_items.append({
                "title": ni.findtext("ht:news_item_title", "", ns),
                "source": ni.findtext("ht:news_item_source", "", ns),
                "url": ni.findtext("ht:news_item_url", "", ns),
            })

        results.append({
            "keyword": keyword,
            "traffic": traffic,
            "picture": picture,
            "news": news_items,
        })

    return results


@_retry_pytrends
def _fetch_interest_over_time(
    keyword: str, timeframe: str, geo: str,
) -> pd.DataFrame:
    pytrends = _build_pytrends()
    pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
    return pytrends.interest_over_time()


def get_interest_over_time(
    keyword: str,
    timeframe: str = "today 12-m",
    geo: str = "JP",
) -> pd.DataFrame:
    """キーワードの検索ボリューム推移を取得する.

    Args:
        keyword: 検索キーワード
        timeframe: 期間（"today 12-m", "today 3-m", "today 1-m" 等）
        geo: 地域コード（JP=日本）

    Returns:
        日付と検索ボリュームのDataFrame

    Raises:
        TrendsRateLimitError: Google からレート制限を受けた場合
    """
    try:
        df = _fetch_interest_over_time(keyword, timeframe, geo)
    except _RATE_LIMIT_EXCEPTIONS as exc:
        if _is_rate_limit(exc):
            raise TrendsRateLimitError(
                "Google Trends のレート制限に達しました。"
                "数分〜数十分待ってから再度お試しください。",
            ) from exc
        raise
    if not df.empty and "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    return df


@_retry_pytrends
def _fetch_related_queries(keyword: str, geo: str) -> dict:
    pytrends = _build_pytrends()
    pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo=geo)
    return pytrends.related_queries()


def get_related_queries(
    keyword: str,
    geo: str = "JP",
) -> dict[str, pd.DataFrame]:
    """関連キーワード（急上昇・人気）を取得する.

    Returns:
        {"rising": DataFrame, "top": DataFrame}

    Raises:
        TrendsRateLimitError: Google からレート制限を受けた場合
    """
    try:
        related = _fetch_related_queries(keyword, geo)
    except _RATE_LIMIT_EXCEPTIONS as exc:
        if _is_rate_limit(exc):
            raise TrendsRateLimitError(
                "Google Trends のレート制限に達しました。"
                "数分〜数十分待ってから再度お試しください。",
            ) from exc
        raise

    return _extract_rising_top(related, keyword)


@_retry_pytrends
def _fetch_related_topics(keyword: str, geo: str) -> dict:
    pytrends = _build_pytrends()
    pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo=geo)
    return pytrends.related_topics()


def get_related_topics(
    keyword: str,
    geo: str = "JP",
) -> dict[str, pd.DataFrame]:
    """関連トピック（急上昇・人気）を取得する.

    Returns:
        {"rising": DataFrame, "top": DataFrame}

    Raises:
        TrendsRateLimitError: Google からレート制限を受けた場合
    """
    try:
        related = _fetch_related_topics(keyword, geo)
    except _RATE_LIMIT_EXCEPTIONS as exc:
        if _is_rate_limit(exc):
            raise TrendsRateLimitError(
                "Google Trends のレート制限に達しました。"
                "数分〜数十分待ってから再度お試しください。",
            ) from exc
        raise

    return _extract_rising_top(related, keyword)


@_retry_pytrends
def _fetch_category_related_queries(
    cat: int, timeframe: str, geo: str,
) -> dict:
    pytrends = _build_pytrends()
    pytrends.build_payload(kw_list=[""], cat=cat, timeframe=timeframe, geo=geo)
    return pytrends.related_queries()


def get_category_related_queries(
    cat: int = 0,
    timeframe: str = "today 12-m",
    geo: str = "JP",
) -> dict[str, pd.DataFrame]:
    """カテゴリ別の人気・急上昇検索ワードを取得する.

    Args:
        cat: Google Trendsカテゴリ番号（0=全体）
        timeframe: 期間
        geo: 地域コード

    Returns:
        {"rising": DataFrame, "top": DataFrame}

    Raises:
        TrendsRateLimitError: Google からレート制限を受けた場合
    """
    try:
        related = _fetch_category_related_queries(cat, timeframe, geo)
    except _RATE_LIMIT_EXCEPTIONS as exc:
        if _is_rate_limit(exc):
            raise TrendsRateLimitError(
                "Google Trends のレート制限に達しました。"
                "数分〜数十分待ってから再度お試しください。",
            ) from exc
        raise

    return _extract_rising_top(related, "")


@_retry_pytrends
def _fetch_category_related_topics(
    cat: int, timeframe: str, geo: str,
) -> dict:
    pytrends = _build_pytrends()
    pytrends.build_payload(kw_list=[""], cat=cat, timeframe=timeframe, geo=geo)
    return pytrends.related_topics()


def get_category_related_topics(
    cat: int = 0,
    timeframe: str = "today 12-m",
    geo: str = "JP",
) -> dict[str, pd.DataFrame]:
    """カテゴリ別の人気・急上昇トピックを取得する.

    Args:
        cat: Google Trendsカテゴリ番号（0=全体）
        timeframe: 期間
        geo: 地域コード

    Returns:
        {"rising": DataFrame, "top": DataFrame}

    Raises:
        TrendsRateLimitError: Google からレート制限を受けた場合
    """
    try:
        related = _fetch_category_related_topics(cat, timeframe, geo)
    except _RATE_LIMIT_EXCEPTIONS as exc:
        if _is_rate_limit(exc):
            raise TrendsRateLimitError(
                "Google Trends のレート制限に達しました。"
                "数分〜数十分待ってから再度お試しください。",
            ) from exc
        raise
    except (IndexError, KeyError):
        logger.warning("カテゴリ別トピック取得でpytrends内部エラー（cat=%d）", cat)
        return {"rising": pd.DataFrame(), "top": pd.DataFrame()}

    return _extract_rising_top(related, "")


def _extract_rising_top(
    related: dict, keyword: str,
) -> dict[str, pd.DataFrame]:
    """pytrends結果からrising/topを安全に抽出する."""
    if keyword not in related:
        return {"rising": pd.DataFrame(), "top": pd.DataFrame()}

    data = related[keyword]
    rising = data.get("rising")
    top = data.get("top")
    return {
        "rising": rising if rising is not None else pd.DataFrame(),
        "top": top if top is not None else pd.DataFrame(),
    }
