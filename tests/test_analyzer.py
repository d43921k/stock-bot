from unittest.mock import MagicMock, patch

import pytest

from stock_bot.analysis.analyzer import analyze_market
from stock_bot.config import Settings
from stock_bot.fetchers.twse import StockQuote

SECTORS = []
NEWS = []
STOCK_POOL = [
    StockQuote(code="2330", name="台積電", close=2510.0, change_points=30.0, change_percent=1.21, trade_value=1.0),
]
GAINER_POOL = [
    StockQuote(code="6999", name="小飆股", close=22.0, change_points=2.0, change_percent=10.0, trade_value=1.0),
]


def _fake_analysis() -> dict:
    return {
        "news_summary": "x",
        "news_conclusion": "y",
        "stock_picks": {
            "short_term": [
                {"ticker": "2330", "name": "台積電", "entry_range": "2480-2520", "stop_loss": "2400", "reason": "r"}
            ],
            "mid_term": [],
            "long_term": [],
        },
        "breakout_picks": [
            {"ticker": "6999", "name": "小飆股", "entry_range": "20-22", "stop_loss": "18", "reason": "r"},
            {"ticker": "9999", "name": "查不到的股票", "entry_range": "1-2", "stop_loss": "0.5", "reason": "r"},
        ],
    }


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
    mock_gemini.analyze_market.return_value = _fake_analysis()
    mock_gemini_cls.return_value = mock_gemini

    result = analyze_market(_settings(), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result["news_summary"] == "x"
    mock_groq_cls.assert_not_called()


@patch("stock_bot.analysis.analyzer.GroqClient")
@patch("stock_bot.analysis.analyzer.GeminiClient")
def test_falls_back_to_groq_when_gemini_fails(mock_gemini_cls, mock_groq_cls):
    mock_gemini = MagicMock()
    mock_gemini.analyze_market.side_effect = RuntimeError("503 UNAVAILABLE")
    mock_gemini_cls.return_value = mock_gemini

    mock_groq = MagicMock()
    mock_groq.analyze_market.return_value = _fake_analysis()
    mock_groq_cls.return_value = mock_groq

    result = analyze_market(_settings(), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result["news_summary"] == "x"
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


@patch("stock_bot.analysis.analyzer.GroqClient")
@patch("stock_bot.analysis.analyzer.GeminiClient")
def test_enriches_picks_with_real_close_price_from_pools(mock_gemini_cls, mock_groq_cls):
    mock_gemini = MagicMock()
    mock_gemini.analyze_market.return_value = _fake_analysis()
    mock_gemini_cls.return_value = mock_gemini

    result = analyze_market(_settings(), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result["stock_picks"]["short_term"][0]["close"] == 2510.0
    assert result["breakout_picks"][0]["close"] == 22.0


@patch("stock_bot.analysis.analyzer.GroqClient")
@patch("stock_bot.analysis.analyzer.GeminiClient")
def test_unknown_ticker_gets_none_close_price(mock_gemini_cls, mock_groq_cls):
    mock_gemini = MagicMock()
    mock_gemini.analyze_market.return_value = _fake_analysis()
    mock_gemini_cls.return_value = mock_gemini

    result = analyze_market(_settings(), SECTORS, NEWS, STOCK_POOL, GAINER_POOL)

    assert result["breakout_picks"][1]["close"] is None
