"""Google Trends APIクライアント（pytrends + RSS）."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd
import requests
from pytrends.request import TrendReq


def get_trending_searches(geo: str = "JP") -> list[dict]:
    """急上昇キーワードを取得する（Google Trends RSSから）.

    Args:
        geo: 地域コード（"JP", "US" 等）

    Returns:
        [{"keyword": str, "traffic": str, "news": [{"title": str, "source": str, "url": str}]}]
    """
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
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
    """
    pytrends = TrendReq(hl="ja-JP", tz=540)
    pytrends.build_payload([keyword], cat=0, timeframe=timeframe, geo=geo)
    df = pytrends.interest_over_time()
    if not df.empty and "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])
    return df


def get_related_queries(
    keyword: str,
    geo: str = "JP",
) -> dict[str, pd.DataFrame]:
    """関連キーワード（急上昇・人気）を取得する.

    Returns:
        {"rising": DataFrame, "top": DataFrame}
    """
    pytrends = TrendReq(hl="ja-JP", tz=540)
    pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo=geo)
    related = pytrends.related_queries()

    result: dict[str, pd.DataFrame] = {}
    if keyword in related:
        rising = related[keyword].get("rising")
        top = related[keyword].get("top")
        result["rising"] = rising if rising is not None else pd.DataFrame()
        result["top"] = top if top is not None else pd.DataFrame()
    else:
        result["rising"] = pd.DataFrame()
        result["top"] = pd.DataFrame()

    return result


def get_related_topics(
    keyword: str,
    geo: str = "JP",
) -> dict[str, pd.DataFrame]:
    """関連トピック（急上昇・人気）を取得する.

    Returns:
        {"rising": DataFrame, "top": DataFrame}
    """
    pytrends = TrendReq(hl="ja-JP", tz=540)
    pytrends.build_payload([keyword], cat=0, timeframe="today 12-m", geo=geo)
    related = pytrends.related_topics()

    result: dict[str, pd.DataFrame] = {}
    if keyword in related:
        rising = related[keyword].get("rising")
        top = related[keyword].get("top")
        result["rising"] = rising if rising is not None else pd.DataFrame()
        result["top"] = top if top is not None else pd.DataFrame()
    else:
        result["rising"] = pd.DataFrame()
        result["top"] = pd.DataFrame()

    return result
