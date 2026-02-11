"""アプリケーションロガー設定."""

from __future__ import annotations

import logging
import sys


def setup_logger(
    name: str = "youtube_analyzer",
    level: int = logging.INFO,
) -> logging.Logger:
    """アプリケーション用ロガーを設定する.

    Args:
        name: ロガー名
        level: ログレベル

    Returns:
        設定済みのLoggerインスタンス
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
