from datetime import datetime

from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote
from stock_bot.fetchers.us_indices import IndexQuote as UsIndexQuote
from stock_bot.report.generator import generate_report, roc_date_to_iso

TW_INDICES = [
    IndexQuote(
        name="發行量加權股價指數",
        date="1151001",
        close=48353.49,
        change_sign="+",
        change_points=413.36,
        change_percent=0.86,
    ),
]
US_INDICES = [
    UsIndexQuote(
        name="道瓊工業指數",
        close=51108.72,
        change_points=182.16,
        change_percent=0.358,
    ),
]
SECTORS = [
    IndexQuote(
        name="半導體類指數",
        date="1151001",
        close=1642.72,
        change_sign="+",
        change_points=18.67,
        change_percent=1.15,
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
ANALYSIS = {
    "news_summary": "新聞摘要測試內容",
    "news_conclusion": "新聞總結測試內容",
    "stock_picks": {
        "short_term": [
            {"ticker": "2330", "name": "台積電", "entry_range": "950-960", "stop_loss": "930", "reason": "短線理由"}
        ],
        "mid_term": [
            {"ticker": "2317", "name": "鴻海", "entry_range": "200-205", "stop_loss": "190", "reason": "中線理由"}
        ],
        "long_term": [
            {"ticker": "2454", "name": "聯發科", "entry_range": "1300-1320", "stop_loss": "1250", "reason": "長線理由"}
        ],
    },
}


def test_roc_date_to_iso():
    assert roc_date_to_iso("1151001") == "2026-10-01"


def test_generate_report_writes_mobile_friendly_html(tmp_path):
    output_path = tmp_path / "index.html"

    result_path = generate_report(
        tw_indices=TW_INDICES,
        us_indices=US_INDICES,
        sectors=SECTORS,
        news=NEWS,
        analysis=ANALYSIS,
        output_path=str(output_path),
        generated_at=datetime(2026, 10, 2, 7, 30),
    )

    html = result_path.read_text(encoding="utf-8")

    assert result_path == output_path
    assert 'name="viewport"' in html
    assert "發行量加權股價指數" in html
    assert "道瓊工業指數" in html
    assert "半導體類指數" in html
    assert "台股大漲創新高" in html
    assert "新聞摘要測試內容" in html
    assert "新聞總結測試內容" in html
    assert "台積電" in html
    assert "950-960" in html
    assert "930" in html
    assert "2026-10-02 07:30" in html


def test_generate_report_creates_parent_dirs(tmp_path):
    nested_path = tmp_path / "nested" / "dir" / "index.html"

    result_path = generate_report(
        tw_indices=TW_INDICES,
        us_indices=US_INDICES,
        sectors=SECTORS,
        news=NEWS,
        analysis=ANALYSIS,
        output_path=str(nested_path),
    )

    assert result_path.exists()
