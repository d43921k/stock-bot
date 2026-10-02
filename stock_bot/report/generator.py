"""把台股資料與 AI 摘要組合成一份行動裝置適用的 HTML 晨報。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote

TEMPLATE_DIR = Path(__file__).parent / "templates"


def _trend(quote: IndexQuote) -> str:
    if quote.is_up:
        return "up"
    if quote.is_down:
        return "down"
    return "flat"


def _quote_to_dict(quote: IndexQuote) -> dict:
    return {
        "name": quote.name,
        "close": quote.close,
        "change_sign": quote.change_sign,
        "change_points": quote.change_points,
        "change_percent": quote.change_percent,
        "trend": _trend(quote),
    }


def roc_date_to_iso(roc_date: str) -> str:
    """把 TWSE 民國日期字串（如 "1151001"）轉成 "2026-10-01"。"""
    year = int(roc_date[:-4]) + 1911
    month = roc_date[-4:-2]
    day = roc_date[-2:]
    return f"{year}-{month}-{day}"


def render_report_html(
    index: IndexQuote,
    sectors: list[IndexQuote],
    news: list[NewsItem],
    ai_summary: str,
    generated_at: datetime | None = None,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")
    generated_at = generated_at or datetime.now()

    return template.render(
        generated_date=roc_date_to_iso(index.date),
        generated_at=generated_at.strftime("%Y-%m-%d %H:%M"),
        index=_quote_to_dict(index),
        sectors=[_quote_to_dict(s) for s in sectors],
        news=news,
        ai_summary=ai_summary,
    )


def generate_report(
    index: IndexQuote,
    sectors: list[IndexQuote],
    news: list[NewsItem],
    ai_summary: str,
    output_path: str,
    generated_at: datetime | None = None,
) -> Path:
    html = render_report_html(index, sectors, news, ai_summary, generated_at)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
