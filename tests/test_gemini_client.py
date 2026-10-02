from unittest.mock import MagicMock, patch

import pytest

from stock_bot.analysis.gemini_client import GeminiClient, build_prompt
from stock_bot.fetchers.news import NewsItem
from stock_bot.fetchers.twse import IndexQuote

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
]
NEWS = [
    NewsItem(
        title="台股大漲創新高",
        link="https://example.com/a",
        published="",
        source="鉅亨網",
    ),
]


def test_build_prompt_includes_key_data():
    prompt = build_prompt(INDEX, SECTORS, NEWS)

    assert "發行量加權股價指數" in prompt
    assert "半導體類指數" in prompt
    assert "台股大漲創新高" in prompt


def test_gemini_client_requires_api_key():
    with pytest.raises(ValueError):
        GeminiClient(api_key="", model="gemini-2.5-flash")


@patch("stock_bot.analysis.gemini_client.genai.Client")
def test_summarize_market_calls_generate_content(mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="  摘要內容  ")
    mock_client_cls.return_value = mock_client

    client = GeminiClient(api_key="fake-key", model="gemini-2.5-flash")
    result = client.summarize_market(INDEX, SECTORS, NEWS)

    assert result == "摘要內容"
    mock_client.models.generate_content.assert_called_once()
    _, kwargs = mock_client.models.generate_content.call_args
    assert kwargs["model"] == "gemini-2.5-flash"
    assert "發行量加權股價指數" in kwargs["contents"]
