"""以 Gemini 為主、Groq 為備援的新聞分析／選股協調邏輯。

Gemini 的免費層偶爾會因伺服器端過載回傳 503，此時自動切換到 Groq（同樣有免費額度，
且幾乎不會過載）重試一次，避免整個晨報產生流程失敗。
"""

from __future__ import annotations

from stock_bot.analysis.gemini_client import GeminiClient
from stock_bot.analysis.groq_client import GroqClient
from stock_bot.config import Settings
from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote, StockQuote


def analyze_market(
    settings: Settings,
    sectors: list[IndexQuote],
    news: list[NewsItem],
    stock_pool: list[StockQuote],
) -> dict:
    try:
        client = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
        return client.analyze_market(sectors, news, stock_pool)
    except Exception as exc:
        if not settings.groq_api_key:
            raise
        print(f"Gemini 呼叫失敗（{exc}），改用 Groq（{settings.groq_model}）重試...")
        fallback_client = GroqClient(api_key=settings.groq_api_key, model=settings.groq_model)
        return fallback_client.analyze_market(sectors, news, stock_pool)
