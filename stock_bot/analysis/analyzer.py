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


def _enrich_with_close_price(
    analysis: dict,
    stock_pool: list[StockQuote],
    gainer_pool: list[StockQuote],
) -> dict:
    """幫每檔選股標的補上收盤價——用我們自己抓到的真實行情查表，不信任 AI 自己報的數字。"""
    price_by_ticker = {q.code: q.close for q in [*stock_pool, *gainer_pool]}
    for picks in analysis["stock_picks"].values():
        for pick in picks:
            pick["close"] = price_by_ticker.get(pick["ticker"])
    for pick in analysis["breakout_picks"]:
        pick["close"] = price_by_ticker.get(pick["ticker"])
    return analysis


def analyze_market(
    settings: Settings,
    sectors: list[IndexQuote],
    news: list[NewsItem],
    stock_pool: list[StockQuote],
    gainer_pool: list[StockQuote],
) -> dict:
    try:
        client = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
        analysis = client.analyze_market(sectors, news, stock_pool, gainer_pool)
    except Exception as exc:
        if not settings.groq_api_key:
            raise
        print(f"Gemini 呼叫失敗（{exc}），改用 Groq（{settings.groq_model}）重試...")
        fallback_client = GroqClient(api_key=settings.groq_api_key, model=settings.groq_model)
        analysis = fallback_client.analyze_market(sectors, news, stock_pool, gainer_pool)

    return _enrich_with_close_price(analysis, stock_pool, gainer_pool)
