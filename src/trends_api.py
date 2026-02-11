"""Google Trends APIクライアント（pytrends + RSS）."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pandas as pd
import requests
from pytrends.request import TrendReq


def get_trending_searches(geo: str = "JP", days: int = 7) -> pd.DataFrame:
    """急上昇キーワードを取得する（Google Trends Daily Trends API）.

    Args:
        geo: 地域コード（"JP", "US" 等）
        days: 取得する日数（1〜7）

    Returns:
        急上昇キーワードのDataFrame（日付・キーワード・検索ボリューム）
    """
    import json
    from datetime import datetime, timedelta

    all_keywords = []
    seen = set()

    for d in range(days):
        target = datetime.now() - timedelta(days=d)
        ed = target.strftime("%Y%m%d")
        url = (
            f"https://trends.google.com/trends/api/dailytrends"
            f"?hl=ja&tz=-540&geo={geo}&ns=15&ed={ed}"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            # レスポンス先頭の ")]}'" を除去
            text = resp.text
            if text.startswith(")]}'"):
                text = text[5:]
            data = json.loads(text)

            trend_days = data.get("default", {}).get("trendingSearchesDays", [])
            for day_data in trend_days:
                date_str = day_data.get("formattedDate", "")
                for search in day_data.get("trendingSearches", []):
                    title = search.get("title", {}).get("query", "")
                    traffic = search.get("formattedTraffic", "")
                    if title and title not in seen:
                        seen.add(title)
                        all_keywords.append({
                            "日付": date_str,
                            "キーワード": title,
                            "検索ボリューム": traffic,
                        })
        except Exception:
            continue

    df = pd.DataFrame(all_keywords)
    if not df.empty:
        df.index = range(1, len(df) + 1)
        df.index.name = "順位"
    return df


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
