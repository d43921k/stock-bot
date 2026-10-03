from unittest.mock import MagicMock, patch

import pytest

from stock_bot.analysis.analyzer import analyze_market
from stock_bot.config import Settings

SECTORS = []
NEWS = []
STOCK_POOL = []
GAINER_POOL = []

FAKE_ANALYSIS = {"news_summary": "x", "news_conclusion": "y", "stock_picks": {}}


def _settings(groq_api_key: str = "groq-key") -> Settings:
    return Settings(
        gemini_api_key="gemini-key",
        gemini_model="gemini-3.5-flash",
        groq_api_key=groq_api_key,
        groq_model="openai/gpt-oss-120b",
        news_query="台股 大盤",
        news_limit=10,
        report_output_path="docs/index.html",
    )


@patch("stock_bot.analysis.analyzer.GroqClient")
@patch("stock_bot.analysis.analyzer.GeminiClient")
def test_uses_gemini_when_it_succeeds(mock_gemini_cls, mock_groq_cls):
    mock_gemini = MagicMock()
    mock_gemini.analyze_market.return_value = FAKE_ANALYSIS
    mock_gemini_cls.return_value = mock_gemini

    result = analyze_market(_settings(), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result == FAKE_ANALYSIS
    mock_groq_cls.assert_not_called()


@patch("stock_bot.analysis.analyzer.GroqClient")
@patch("stock_bot.analysis.analyzer.GeminiClient")
def test_falls_back_to_groq_when_gemini_fails(mock_gemini_cls, mock_groq_cls):
    mock_gemini = MagicMock()
    mock_gemini.analyze_market.side_effect = RuntimeError("503 UNAVAILABLE")
    mock_gemini_cls.return_value = mock_gemini

    mock_groq = MagicMock()
    mock_groq.analyze_market.return_value = FAKE_ANALYSIS
    mock_groq_cls.return_value = mock_groq

    result = analyze_market(_settings(), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result == FAKE_ANALYSIS
    mock_groq.analyze_market.assert_called_once_with(SECTORS, NEWS, STOCK_POOL, GAINER_POOL)


@patch("stock_bot.analysis.analyzer.GroqClient")
@patch("stock_bot.analysis.analyzer.GeminiClient")
def test_reraises_when_gemini_fails_and_no_groq_key(mock_gemini_cls, mock_groq_cls):
    mock_gemini = MagicMock()
    mock_gemini.analyze_market.side_effect = RuntimeError("503 UNAVAILABLE")
    mock_gemini_cls.return_value = mock_gemini

    with pytest.raises(RuntimeError):
        analyze_market(_settings(groq_api_key=""), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    mock_groq_cls.assert_not_called()
