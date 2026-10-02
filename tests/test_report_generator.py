from datetime import datetime

from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote
from stock_bot.report.generator import generate_report, roc_date_to_iso

INDEX = IndexQuote(
    name="發行量加權股價指數",
    date="1151001",
    close=48353.49,
    change_sign="+",
    change_points=413.36,
    change_percent=0.86,
)
SECTORS = [
    IndexQuote(
        name="半導體類指數",
        date="1151001",
        close=1642.72,
        change_sign="+",
        change_points=18.67,
        change_percent=1.15,
    ),
    IndexQuote(
        name="航運類指數",
        date="1151001",
        close=209.36,
        change_sign="-",
        change_points=1.58,
        change_percent=-0.75,
    ),
]
NEWS = [
    NewsItem(
        title="台股大漲創新高",
        link="https://example.com/a",
        published="",
        source="鉅亨網",
    ),
]


def test_roc_date_to_iso():
    assert roc_date_to_iso("1151001") == "2026-10-01"


def test_generate_report_writes_mobile_friendly_html(tmp_path):
    output_path = tmp_path / "index.html"

    result_path = generate_report(
        index=INDEX,
        sectors=SECTORS,
        news=NEWS,
        ai_summary="大盤今日上漲，半導體表現強勢。",
        output_path=str(output_path),
        generated_at=datetime(2026, 10, 2, 7, 30),
    )

    html = result_path.read_text(encoding="utf-8")

    assert result_path == output_path
    assert 'name="viewport"' in html
    assert "發行量加權股價指數" in html
    assert "半導體類指數" in html
    assert "台股大漲創新高" in html
    assert "大盤今日上漲，半導體表現強勢。" in html
    assert "2026-10-02 07:30" in html


def test_generate_report_creates_parent_dirs(tmp_path):
    nested_path = tmp_path / "nested" / "dir" / "index.html"

    result_path = generate_report(
        index=INDEX,
        sectors=SECTORS,
        news=NEWS,
        ai_summary="測試摘要",
        output_path=str(nested_path),
    )

    assert result_path.exists()
