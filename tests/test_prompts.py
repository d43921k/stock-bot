from stock_bot.analysis.prompts import build_prompt
from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote, StockQuote

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
STOCK_POOL = [
    StockQuote(
        code="2308",
        name="台達電",
        close=1905.0,
        change_points=15.0,
        change_percent=0.79,
        trade_value=11586905180.0,
    ),
]


def test_build_prompt_includes_key_data():
    prompt = build_prompt(SECTORS, NEWS, STOCK_POOL)

    assert "半導體類指數" in prompt
    assert "台股大漲創新高" in prompt
    assert "2308" in prompt
    assert "1905.0" in prompt
