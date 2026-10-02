from unittest.mock import MagicMock, patch

from stock_bot.fetchers import twse

SAMPLE_ROWS = [
    {
        "日期": "1151001",
        "指數": "發行量加權股價指數",
        "收盤指數": "48353.49",
        "漲跌": "+",
        "漲跌點數": "413.36",
        "漲跌百分比": "0.86",
        "特殊處理註記": "",
    },
    {
        "日期": "1151001",
        "指數": "半導體類指數",
        "收盤指數": "1642.72",
        "漲跌": "+",
        "漲跌點數": "18.67",
        "漲跌百分比": "1.15",
        "特殊處理註記": "",
    },
    {
        "日期": "1151001",
        "指數": "航運類指數",
        "收盤指數": "209.36",
        "漲跌": "-",
        "漲跌百分比": "-0.75",
        "漲跌點數": "1,211.58",
        "特殊處理註記": "",
    },
    {
        "日期": "1151001",
        "指數": "半導體類報酬指數",
        "收盤指數": "3150.97",
        "漲跌": "+",
        "漲跌點數": "38.5",
        "漲跌百分比": "1.15",
        "特殊處理註記": "",
    },
]


def _mock_response():
    mock_resp = MagicMock()
    mock_resp.json.return_value = SAMPLE_ROWS
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_weighted_index(mock_get):
    mock_get.return_value = _mock_response()

    quote = twse.fetch_weighted_index()

    assert quote.name == "發行量加權股價指數"
    assert quote.close == 48353.49
    assert quote.is_up is True
    assert quote.change_percent == 0.86


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_sector_indices_excludes_return_index_variants(mock_get):
    mock_get.return_value = _mock_response()

    sectors = twse.fetch_sector_indices()
    names = [s.name for s in sectors]

    assert "半導體類指數" in names
    assert "航運類指數" in names
    assert "半導體類報酬指數" not in names
    assert "發行量加權股價指數" not in names


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_sector_indices_sorted_by_change_percent_desc(mock_get):
    mock_get.return_value = _mock_response()

    sectors = twse.fetch_sector_indices()

    percents = [s.change_percent for s in sectors]
    assert percents == sorted(percents, reverse=True)


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_sector_indices_top_n(mock_get):
    mock_get.return_value = _mock_response()

    sectors = twse.fetch_sector_indices(top_n=1)

    assert len(sectors) == 1


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_weighted_index_missing_raises(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = []
    mock_resp.raise_for_status.return_value = None
    mock_get.return_value = mock_resp

    try:
        twse.fetch_weighted_index()
        assert False, "應該要拋出 ValueError"
    except ValueError:
        pass


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_named_indices_preserves_requested_order(mock_get):
    mock_get.return_value = _mock_response()

    quotes = twse.fetch_named_indices(["航運類指數", "發行量加權股價指數"])

    assert [q.name for q in quotes] == ["航運類指數", "發行量加權股價指數"]


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_named_indices_skips_unknown_names(mock_get):
    mock_get.return_value = _mock_response()

    quotes = twse.fetch_named_indices(["發行量加權股價指數", "不存在的指數"])

    assert [q.name for q in quotes] == ["發行量加權股價指數"]
