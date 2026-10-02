"""串接 Google Gemini API，將台股資料摘要成一段盤勢分析文字。"""

from __future__ import annotations

from google import genai

from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote

SYSTEM_INSTRUCTION = (
    "你是一位專業的台股盤勢分析師，擅長用簡潔易懂的繁體中文，"
    "為忙碌的投資人撰寫每日晨報。語氣專業、客觀，避免過度誇大或提供明確買賣建議。"
)


def build_prompt(
    index: IndexQuote,
    sectors: list[IndexQuote],
    news: list[NewsItem],
) -> str:
    sector_lines = "\n".join(
        f"- {s.name}：{s.change_sign}{s.change_percent}%（收盤 {s.close}）" for s in sectors
    )
    news_lines = "\n".join(f"- {n.title}（{n.source or '未知來源'}）" for n in news)

    return f"""請根據以下資料，撰寫今日台股晨報摘要，包含三個段落：
1.「大盤觀察」：解讀加權指數漲跌意涵
2.「焦點族群」：點出表現最強與最弱的類股，並簡述可能原因
3.「新聞重點」：統整財經新聞的共同主題或值得留意的風險

請用 3~5 句精簡繁體中文撰寫每個段落，總長度控制在 400 字以內，不要加入任何投資建議或目標價。

【加權指數】
{index.name}：收盤 {index.close}，{index.change_sign}{index.change_points} 點（{index.change_sign}{index.change_percent}%）

【類股漲跌幅（由高到低）】
{sector_lines}

【相關新聞標題】
{news_lines}
"""


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("缺少 GEMINI_API_KEY，請在 .env 檔案中設定")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def summarize_market(
        self,
        index: IndexQuote,
        sectors: list[IndexQuote],
        news: list[NewsItem],
    ) -> str:
        prompt = build_prompt(index, sectors, news)
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config={"system_instruction": SYSTEM_INSTRUCTION},
        )
        return (response.text or "").strip()
