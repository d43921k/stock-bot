"""Gemini／Groq 共用的系統提示詞與使用者 prompt 組裝邏輯。"""

from __future__ import annotations

from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote, StockQuote

SYSTEM_INSTRUCTION = (
    "你是一位專業的台股盤勢分析師，擅長用簡潔易懂的繁體中文，"
    "為忙碌的投資人撰寫每日晨報並挑選潛力股。語氣專業、客觀，"
    "避免過度誇大或保證獲利的言論，所有進場區間與防守價格僅供參考，不構成投資建議。"
    "選股時務必以題目提供的「個股參考行情」中的實際收盤價為準，"
    "絕對不要使用你自己記憶中可能過時的股價，進場區間與防守價必須貼近所提供的實際收盤價量級。"
)


def _format_stock_lines(stock_pool: list[StockQuote]) -> str:
    return "\n".join(
        f"- {s.code} {s.name}：收盤 {s.close}，{'+' if s.change_points >= 0 else ''}{s.change_percent:.2f}%"
        for s in stock_pool
    )


def build_prompt(
    sectors: list[IndexQuote],
    news: list[NewsItem],
    stock_pool: list[StockQuote],
    gainer_pool: list[StockQuote],
) -> str:
    sector_lines = "\n".join(
        f"- {s.name}：{s.change_sign}{s.change_percent}%" for s in sectors
    )
    news_lines = "\n".join(f"- {n.title}（{n.source or '未知來源'}）" for n in news)
    stock_lines = _format_stock_lines(stock_pool)
    gainer_lines = _format_stock_lines(gainer_pool)

    return f"""請根據以下台股當日資料，完成「新聞分析」與「潛力股推薦」。

【焦點族群（漲幅前五）】
{sector_lines}

【相關財經新聞標題】
{news_lines}

【個股參考行情（依成交金額排序，今日實際收盤價，單位：元）】
{stock_lines}

【當日漲幅最高個股（動能強勢股，今日實際收盤價，單位：元）】
{gainer_lines}

請完成：
1. news_summary：統整上述新聞的重點與共同主題（150 字以內）
2. news_conclusion：給出今日新聞的總結與值得留意的風險（100 字以內）
3. stock_picks：根據今日焦點族群、新聞與上方「個股參考行情」，分別挑選
   「短線（1-2 週）」「中線（1-3 個月）」「長線（半年以上）」各剛好 5 檔台股潛力股
   （請優先從個股參考行情清單中選擇，確保股價真實可信），每檔提供股票代號、名稱、
   建議進場價格區間、建議防守價格（跌破應停損）、30 字以內選股理由。
   進場區間與防守價務必貼近該股票在「個股參考行情」中的實際收盤價，不可憑記憶捏造不符實際價格量級的數字。
4. breakout_picks：從「當日漲幅最高個股」清單中，挑選剛好 3 檔短期內最有機會
   延續動能、漲幅有機會超過 50% 的高風險爆發股（通常是題材驅動、成交量放大的中小型股），
   每檔同樣提供股票代號、名稱、建議進場價格區間、建議防守價格、30 字以內選股理由
   （理由應說明爆發的題材或動能依據）。這類標的波動劇烈，請在理由中明確提醒風險極高。

不要提供明確目標價或保證獲利的言論，所有建議僅供參考。
"""
