"""抓取財經新聞（透過 Google 新聞 RSS，免 API Key）。"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import feedparser

GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?q={query}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"


@dataclass(frozen=True)
class NewsItem:
    title: str
    link: str
    published: str
    source: str


def _parse_entry(entry) -> NewsItem:
    source = ""
    if "source" in entry and getattr(entry.source, "title", None):
        source = entry.source.title
    return NewsItem(
        title=entry.get("title", ""),
        link=entry.get("link", ""),
        published=entry.get("published", ""),
        source=source,
    )


def fetch_news(query: str = "台股 大盤", limit: int = 10) -> list[NewsItem]:
    """用 Google 新聞 RSS 搜尋財經新聞，回傳最新 `limit` 則。"""
    url = GOOGLE_NEWS_RSS_URL.format(query=quote(query))
    feed = feedparser.parse(url)
    return [_parse_entry(entry) for entry in feed.entries[:limit]]
