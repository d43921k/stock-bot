"""晨報產生流程進入點：抓資料 -> Gemini 摘要 -> 產生 HTML。

執行方式：
    python -m stock_bot.main
"""

from __future__ import annotations

from datetime import datetime

from stock_bot.analysis.gemini_client import GeminiClient
from stock_bot.config import load_settings
from stock_bot.fetchers.news import fetch_news
from stock_bot.fetchers.twse import fetch_sector_indices, fetch_weighted_index
from stock_bot.report.generator import generate_report


def run() -> str:
    settings = load_settings()

    print("抓取加權指數...")
    index = fetch_weighted_index()
    print(f"  {index.name}：{index.change_sign}{index.change_percent}%（收盤 {index.close}）")

    print("抓取類股指數...")
    sectors = fetch_sector_indices()
    print(f"  共 {len(sectors)} 個類股")

    print(f"抓取新聞（關鍵字：{settings.news_query}）...")
    news = fetch_news(query=settings.news_query, limit=settings.news_limit)
    print(f"  共 {len(news)} 則新聞")

    print(f"呼叫 Gemini（{settings.gemini_model}）產生摘要...")
    client = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model)
    top_sectors = sectors[:5] + sectors[-5:] if len(sectors) > 10 else sectors
    ai_summary = client.summarize_market(index, top_sectors, news)

    print(f"產生 HTML 晨報 -> {settings.report_output_path}")
    output_path = generate_report(
        index=index,
        sectors=sectors,
        news=news,
        ai_summary=ai_summary,
        output_path=settings.report_output_path,
        generated_at=datetime.now(),
    )

    print(f"完成！晨報已輸出至：{output_path}")
    return str(output_path)


if __name__ == "__main__":
    run()
