from unittest.mock import MagicMock, patch

from stock_bot.fetchers import us_indices


def _mock_response(close: float, full_day_change: float, change_percent: float):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": close,
                        "fulldayChange": full_day_change,
                        "regularMarketChangePercent": change_percent,
                    }
                }
            ]
        }
    }
    return mock_resp


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_returns_all_symbols(mock_get):
    mock_get.return_value = _mock_response(51108.72, 182.16, 0.358)

    quotes = us_indices.fetch_us_indices()

    assert len(quotes) == len(us_indices.US_INDEX_SYMBOLS)
    names = [q.name for q in quotes]
    assert "道瓊工業指數" in names
    assert "S&P 500" in names
    assert "那斯達克綜合指數" in names


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_up_day(mock_get):
    mock_get.return_value = _mock_response(51108.72, 182.16, 0.358)

    quotes = us_indices.fetch_us_indices()

    quote = quotes[0]
    assert quote.change_points == 182.16
    assert quote.change_percent == 0.358
    assert quote.is_up is True
    assert quote.change_sign == "+"


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_down_day(mock_get):
    mock_get.return_value = _mock_response(50000.0, -200.0, -0.4)

    quotes = us_indices.fetch_us_indices()

    quote = quotes[0]
    assert quote.is_down is True
    assert quote.change_sign == "-"


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_change_points_and_percent_agree_in_sign(mock_get):
    """change_points 與 change_percent 必須同方向，避免兩個欄位各說各話。"""
    mock_get.return_value = _mock_response(50000.0, -200.0, -0.4)

    quotes = us_indices.fetch_us_indices()

    quote = quotes[0]
    assert (quote.change_points < 0) == (quote.change_percent < 0)
