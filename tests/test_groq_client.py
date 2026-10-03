import json
from unittest.mock import MagicMock, patch

import pytest

from stock_bot.analysis.groq_client import GroqClient
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
GAINER_POOL = [
    StockQuote(
        code="6999",
        name="小飆股",
        close=22.0,
        change_points=2.0,
        change_percent=10.0,
        trade_value=50000000.0,
    ),
]

FAKE_ANALYSIS = {
    "news_summary": "新聞摘要測試內容",
    "news_conclusion": "新聞總結測試內容",
    "stock_picks": {
        "short_term": [{"ticker": "2330", "name": "台積電", "entry_range": "950-960", "stop_loss": "930", "reason": "測試理由"}],
        "mid_term": [],
        "long_term": [],
    },
    "breakout_picks": [
        {"ticker": "6999", "name": "小飆股", "entry_range": "20-22", "stop_loss": "18", "reason": "測試爆發理由"}
    ],
}


def test_groq_client_requires_api_key():
    with pytest.raises(ValueError):
        GroqClient(api_key="", model="openai/gpt-oss-120b")


@patch("stock_bot.analysis.groq_client.Groq")
def test_analyze_market_calls_chat_completions_with_strict_schema(mock_groq_cls):
    mock_client = MagicMock()
    mock_message = MagicMock(content=json.dumps(FAKE_ANALYSIS))
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=mock_message)]
    )
    mock_groq_cls.return_value = mock_client

    client = GroqClient(api_key="fake-key", model="openai/gpt-oss-120b")
    result = client.analyze_market(SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result == FAKE_ANALYSIS
    mock_client.chat.completions.create.assert_called_once()
    _, kwargs = mock_client.chat.completions.create.call_args
    assert kwargs["model"] == "openai/gpt-oss-120b"
    assert kwargs["response_format"]["json_schema"]["strict"] is True
    assert "breakout_picks" in kwargs["response_format"]["json_schema"]["schema"]["properties"]
    user_message = next(m["content"] for m in kwargs["messages"] if m["role"] == "user")
    assert "半導體類指數" in user_message
    assert "2308" in user_message
    assert "6999" in user_message
