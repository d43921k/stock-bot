"""串接 Google Gemini API：彙整財經新聞摘要，並挑選短中長線潛力股。"""

from __future__ import annotations

import json

from google import genai

from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote, StockQuote

SYSTEM_INSTRUCTION = (
    "你是一位專業的台股盤勢分析師，擅長用簡潔易懂的繁體中文，"
    "為忙碌的投資人撰寫每日晨報並挑選潛力股。語氣專業、客觀，"
    "避免過度誇大或保證獲利的言論，所有進場區間與防守價格僅供參考，不構成投資建議。"
    "選股時務必以題目提供的「個股參考行情」中的實際收盤價為準，"
    "絕對不要使用你自己記憶中可能過時的股價，進場區間與防守價必須貼近所提供的實際收盤價量級。"
)

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


def build_prompt(
    sectors: list[IndexQuote],
    news: list[NewsItem],
    stock_pool: list[StockQuote],
) -> str:
    sector_lines = "\n".join(
        f"- {s.name}：{s.change_sign}{s.change_percent}%" for s in sectors
    )
    news_lines = "\n".join(f"- {n.title}（{n.source or '未知來源'}）" for n in news)
    stock_lines = "\n".join(
        f"- {s.code} {s.name}：收盤 {s.close}，{'+' if s.change_points >= 0 else ''}{s.change_percent:.2f}%"
        for s in stock_pool
    )

    return f"""請根據以下台股當日資料，完成「新聞分析」與「潛力股推薦」。

【焦點族群（漲幅前五）】
{sector_lines}

【相關財經新聞標題】
{news_lines}

【個股參考行情（依成交金額排序，今日實際收盤價，單位：元）】
{stock_lines}

請完成：
1. news_summary：統整上述新聞的重點與共同主題（150 字以內）
2. news_conclusion：給出今日新聞的總結與值得留意的風險（100 字以內）
3. stock_picks：根據今日焦點族群、新聞與上方「個股參考行情」，分別挑選
   「短線（1-2 週）」「中線（1-3 個月）」「長線（半年以上）」各 5 檔台股潛力股
   （請優先從個股參考行情清單中選擇，確保股價真實可信），每檔提供股票代號、名稱、
   建議進場價格區間、建議防守價格（跌破應停損）、30 字以內選股理由。
   進場區間與防守價務必貼近該股票在「個股參考行情」中的實際收盤價，不可憑記憶捏造不符實際價格量級的數字。

不要提供明確目標價或保證獲利的言論，所有建議僅供參考。
"""


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
