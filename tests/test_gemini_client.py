from unittest.mock import MagicMock, patch

import pytest

from stock_bot.analysis.gemini_client import GeminiClient, build_prompt
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

FAKE_ANALYSIS = {
    "news_summary": "新聞摘要測試內容",
    "news_conclusion": "新聞總結測試內容",
    "stock_picks": {
        "short_term": [{"ticker": "2330", "name": "台積電", "entry_range": "950-960", "stop_loss": "930", "reason": "測試理由"}],
        "mid_term": [],
        "long_term": [],
    },
}


def test_build_prompt_includes_key_data():
    prompt = build_prompt(SECTORS, NEWS, STOCK_POOL)

    assert "半導體類指數" in prompt
    assert "台股大漲創新高" in prompt
    assert "2308" in prompt
    assert "1905.0" in prompt


def test_gemini_client_requires_api_key():
    with pytest.raises(ValueError):
        GeminiClient(api_key="", model="gemini-3.5-flash")


@patch("stock_bot.analysis.gemini_client.genai.Client")
def test_analyze_market_calls_generate_content_with_schema(mock_client_cls):
    import json

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text=json.dumps(FAKE_ANALYSIS))
    mock_client_cls.return_value = mock_client

    client = GeminiClient(api_key="fake-key", model="gemini-3.5-flash")
    result = client.analyze_market(SECTORS, NEWS, STOCK_POOL)

    assert result == FAKE_ANALYSIS
    mock_client.models.generate_content.assert_called_once()
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-3.5-flash"
    assert kwargs["config"]["response_mime_type"] == "application/json"
    assert "半導體類指數" in kwargs["contents"]
    assert "2308" in kwargs["contents"]
