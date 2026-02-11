"""Google Trends APIクライアント（pytrends）."""

from __future__ import annotations

import pandas as pd
from pytrends.request import TrendReq


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
