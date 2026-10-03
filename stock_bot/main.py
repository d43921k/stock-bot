"""晨報產生流程進入點：抓資料 -> AI 分析/選股（Gemini，失敗則備援 Groq） -> 產生 HTML。

執行方式：
    python -m stock_bot.main
"""

from __future__ import annotations

from datetime import datetime

from stock_bot.analysis.analyzer import analyze_market
from stock_bot.config import load_settings
from stock_bot.fetchers.news import fetch_news
from stock_bot.fetchers.twse import fetch_named_indices, fetch_sector_indices, fetch_top_stocks_by_value
from stock_bot.fetchers.us_indices import fetch_us_indices
from stock_bot.report.generator import generate_report

TW_DASHBOARD_INDEX_NAMES = ["發行量加權股價指數", "臺灣50指數", "臺灣高股息指數"]
SECTOR_TOP_N = 5
STOCK_POOL_TOP_N = 60


def run() -> str:
    settings = load_settings()

    print("抓取台股指數...")
    tw_indices = fetch_named_indices(TW_DASHBOARD_INDEX_NAMES)
    for q in tw_indices:
        print(f"  {q.name}：{q.change_sign}{abs(q.change_percent):.2f}%（收盤 {q.close:.2f}）")

    print("抓取美股指數...")
    us_indices = fetch_us_indices()
    for q in us_indices:
        print(f"  {q.name}：{q.change_sign}{abs(q.change_percent):.2f}%（收盤 {q.close:.2f}）")

    print(f"抓取焦點族群（前 {SECTOR_TOP_N}）...")
    sectors = fetch_sector_indices(top_n=SECTOR_TOP_N)

    print(f"抓取新聞（關鍵字：{settings.news_query}）...")
    news = fetch_news(query=settings.news_query, limit=settings.news_limit)
    print(f"  共 {len(news)} 則新聞")

    print(f"抓取個股參考行情（依成交金額前 {STOCK_POOL_TOP_N}）...")
    stock_pool = fetch_top_stocks_by_value(top_n=STOCK_POOL_TOP_N)
    print(f"  共 {len(stock_pool)} 檔個股")

    print(f"呼叫 Gemini（{settings.gemini_model}）分析新聞並挑選潛力股...")
    analysis = analyze_market(settings, sectors=sectors, news=news, stock_pool=stock_pool)

    print(f"產生 HTML 晨報 -> {settings.report_output_path}")
    output_path = generate_report(
        tw_indices=tw_indices,
        us_indices=us_indices,
        sectors=sectors,
        news=news,
        analysis=analysis,
        output_path=settings.report_output_path,
        generated_at=datetime.now(),
    )

    print(f"完成！晨報已輸出至：{output_path}")
    return str(output_path)


if __name__ == "__main__":
    run()
