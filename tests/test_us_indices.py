from unittest.mock import MagicMock, patch

from stock_bot.fetchers import us_indices


def _mock_response(close: float, prev_close: float, change_percent: float):
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "chart": {
            "result": [
                {
                    "meta": {
                        "regularMarketPrice": close,
                        "chartPreviousClose": prev_close,
                        "regularMarketChangePercent": change_percent,
                    }
                }
            ]
        }
    }
    return mock_resp


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_returns_all_symbols(mock_get):
    mock_get.return_value = _mock_response(51108.72, 50926.56, 0.358)

    quotes = us_indices.fetch_us_indices()

    assert len(quotes) == len(us_indices.US_INDEX_SYMBOLS)
    names = [q.name for q in quotes]
    assert "道瓊工業指數" in names
    assert "S&P 500" in names
    assert "那斯達克綜合指數" in names


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_computes_change_points_and_sign(mock_get):
    mock_get.return_value = _mock_response(51108.72, 50926.56, 0.358)

    quotes = us_indices.fetch_us_indices()

    quote = quotes[0]
    assert round(quote.change_points, 2) == round(51108.72 - 50926.56, 2)
    assert quote.is_up is True
    assert quote.change_sign == "+"


@patch("stock_bot.fetchers.us_indices.requests.get")
def test_fetch_us_indices_down_day(mock_get):
    mock_get.return_value = _mock_response(50000.0, 50200.0, -0.4)

    quotes = us_indices.fetch_us_indices()

    quote = quotes[0]
    assert quote.is_down is True
    assert quote.change_sign == "-"
