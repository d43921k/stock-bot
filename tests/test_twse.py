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


STOCK_DAY_ALL_ROWS = [
    {
        "Date": "1151001",
        "Code": "2308",
        "Name": "台達電",
        "TradeVolume": "6119811",
        "TradeValue": "11586905180",
        "OpeningPrice": "1925.00",
        "HighestPrice": "1935.00",
        "LowestPrice": "1860.00",
        "ClosingPrice": "1905.00",
        "Change": "15.0000",
        "Transaction": "26647",
    },
    {
        "Date": "1151001",
        "Code": "2330",
        "Name": "台積電",
        "TradeVolume": "20000000",
        "TradeValue": "50000000000",
        "ClosingPrice": "2510.00",
        "Change": "30.0000",
        "Transaction": "1",
    },
    {
        "Date": "1151001",
        "Code": "0050",
        "Name": "元大台灣50",
        "TradeVolume": "1000000",
        "TradeValue": "9999999999",
        "ClosingPrice": "60.00",
        "Change": "0.5000",
        "Transaction": "1",
    },
    {
        "Date": "1151001",
        "Code": "00625K",
        "Name": "富邦上証+R",
        "TradeVolume": "",
        "TradeValue": "",
        "ClosingPrice": "",
        "Change": "0.0000",
        "Transaction": "",
    },
]


def _mock_stock_day_all_response():
    mock_resp = MagicMock()
    mock_resp.json.return_value = STOCK_DAY_ALL_ROWS
    mock_resp.raise_for_status.return_value = None
    return mock_resp


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_top_stocks_by_value_excludes_etf_and_halted(mock_get):
    mock_get.return_value = _mock_stock_day_all_response()

    quotes = twse.fetch_top_stocks_by_value(top_n=10)
    codes = [q.code for q in quotes]

    assert "2308" in codes
    assert "2330" in codes
    assert "0050" not in codes  # ETF（00 開頭）
    assert "00625K" not in codes  # 無交易資料


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_top_stocks_by_value_sorted_by_trade_value_desc(mock_get):
    mock_get.return_value = _mock_stock_day_all_response()

    quotes = twse.fetch_top_stocks_by_value(top_n=10)

    assert quotes[0].code == "2330"  # 成交金額最高


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_top_stocks_by_value_computes_real_close_and_percent(mock_get):
    mock_get.return_value = _mock_stock_day_all_response()

    quotes = twse.fetch_top_stocks_by_value(top_n=10)
    delta = next(q for q in quotes if q.code == "2308")

    assert delta.close == 1905.00
    assert delta.name == "台達電"
    assert round(delta.change_percent, 2) == round(15 / (1905 - 15) * 100, 2)


@patch("stock_bot.fetchers.twse.requests.get")
def test_fetch_top_stocks_by_value_respects_top_n(mock_get):
    mock_get.return_value = _mock_stock_day_all_response()

    quotes = twse.fetch_top_stocks_by_value(top_n=1)

    assert len(quotes) == 1
