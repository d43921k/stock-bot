"""讀取 .env 設定值，提供整個專案共用的設定物件。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    news_query: str
    news_limit: int
    report_output_path: str


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        news_query=os.getenv("NEWS_QUERY", "台股 大盤"),
        news_limit=int(os.getenv("NEWS_LIMIT", "10")),
        report_output_path=os.getenv("REPORT_OUTPUT_PATH", "docs/index.html"),
    )
