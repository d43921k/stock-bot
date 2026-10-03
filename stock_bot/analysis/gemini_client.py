"""串接 Google Gemini API：彙整財經新聞摘要，並挑選短中長線潛力股。"""

from __future__ import annotations

import json

from google import genai

from stock_bot.analysis.prompts import SYSTEM_INSTRUCTION, build_prompt
from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote, StockQuote

_STOCK_PICK_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string", "description": "股票代號，例如 2330"},
        "name": {"type": "string", "description": "股票名稱"},
        "entry_range": {"type": "string", "description": "建議進場價格區間，例如 950-960"},
        "stop_loss": {"type": "string", "description": "建議防守價格（跌破應停損）"},
        "reason": {"type": "string", "description": "選股理由，30 字以內"},
    },
    "required": ["ticker", "name", "entry_range", "stop_loss", "reason"],
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "news_summary": {"type": "string", "description": "財經新聞重點摘要，150 字以內"},
        "news_conclusion": {"type": "string", "description": "新聞總結與風險提醒，100 字以內"},
        "stock_picks": {
            "type": "object",
            "properties": {
                "short_term": {
                    "type": "array",
                    "items": _STOCK_PICK_SCHEMA,
                    "minItems": 5,
                    "maxItems": 5,
                },
                "mid_term": {
                    "type": "array",
                    "items": _STOCK_PICK_SCHEMA,
                    "minItems": 5,
                    "maxItems": 5,
                },
                "long_term": {
                    "type": "array",
                    "items": _STOCK_PICK_SCHEMA,
                    "minItems": 5,
                    "maxItems": 5,
                },
            },
            "required": ["short_term", "mid_term", "long_term"],
        },
    },
    "required": ["news_summary", "news_conclusion", "stock_picks"],
}


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("缺少 GEMINI_API_KEY，請在 .env 檔案中設定")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def analyze_market(
        self,
        sectors: list[IndexQuote],
        news: list[NewsItem],
        stock_pool: list[StockQuote],
    ) -> dict:
        prompt = build_prompt(sectors, news, stock_pool)
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={
                "system_instruction": SYSTEM_INSTRUCTION,
                "response_mime_type": "application/json",
                "response_schema": RESPONSE_SCHEMA,
            },
        )
        return json.loads(response.text)
