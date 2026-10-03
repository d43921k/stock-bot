"""串接 Groq API（OpenAI 相容格式）：Gemini 的備援方案。

Groq 用自家 LPU 硬體跑推論，速度快且很少發生伺服器過載，免費額度對每日一次的
排程用量綽綽有餘。`openai/gpt-oss-120b` 支援 strict JSON schema（強制輸出符合格式）。

注意：strict 模式要求每個 object 都要有 additionalProperties: false，且所有屬性都
必須列在 required 中；不支援 minItems/maxItems，因此「剛好 5 檔」的要求改由
prompts.build_prompt() 的文字指示來約束。
"""

from __future__ import annotations

import json

from groq import Groq

from stock_bot.analysis.prompts import SYSTEM_INSTRUCTION, build_prompt
from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote, StockQuote

_STOCK_PICK_SCHEMA = {
    "type": "object",
    "properties": {
        "ticker": {"type": "string"},
        "name": {"type": "string"},
        "entry_range": {"type": "string"},
        "stop_loss": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["ticker", "name", "entry_range", "stop_loss", "reason"],
    "additionalProperties": False,
}

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "news_summary": {"type": "string"},
        "news_conclusion": {"type": "string"},
        "stock_picks": {
            "type": "object",
            "properties": {
                "short_term": {"type": "array", "items": _STOCK_PICK_SCHEMA},
                "mid_term": {"type": "array", "items": _STOCK_PICK_SCHEMA},
                "long_term": {"type": "array", "items": _STOCK_PICK_SCHEMA},
            },
            "required": ["short_term", "mid_term", "long_term"],
            "additionalProperties": False,
        },
        "breakout_picks": {"type": "array", "items": _STOCK_PICK_SCHEMA},
    },
    "required": ["news_summary", "news_conclusion", "stock_picks", "breakout_picks"],
    "additionalProperties": False,
}


class GroqClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("缺少 GROQ_API_KEY，請在 .env 檔案中設定")
        self._client = Groq(api_key=api_key)
        self._model = model

    def analyze_market(
        self,
        sectors: list[IndexQuote],
        news: list[NewsItem],
        stock_pool: list[StockQuote],
        gainer_pool: list[StockQuote],
    ) -> dict:
        prompt = build_prompt(sectors, news, stock_pool, gainer_pool)
        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "market_analysis",
                    "strict": True,
                    "schema": RESPONSE_SCHEMA,
                },
            },
        )
        return json.loads(completion.choices[0].message.content)
