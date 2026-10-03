"""抓取台灣證券交易所（TWSE）OpenAPI 的大盤指數、類股指數與個股行情。

資料來源：
- https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX（大盤與類股指數）
- https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL（全市場個股當日收盤行情）
（皆為公開資料，不需要 API Key）
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

MI_INDEX_URL = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
STOCK_DAY_ALL_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
WEIGHTED_INDEX_NAME = "發行量加權股價指數"
REQUEST_TIMEOUT = 10


@dataclass(frozen=True)
class IndexQuote:
    name: str
    date: str
    close: float
    change_sign: str  # "+"、"-" 或空字串（平盤）
    change_points: float
    change_percent: float

    @property
    def is_up(self) -> bool:
        return self.change_sign == "+"

    @property
    def is_down(self) -> bool:
        return self.change_sign == "-"


@dataclass(frozen=True)
class StockQuote:
    code: str
    name: str
    close: float
    change_points: float
    change_percent: float
    trade_value: float


def _to_float(value: str) -> float:
    value = (value or "").replace(",", "").strip()
    if not value or value == "--":
        return 0.0
    return float(value)


def _parse_quote(row: dict) -> IndexQuote:
    return IndexQuote(
        name=row["指數"],
        date=row["日期"],
        close=_to_float(row["收盤指數"]),
        change_sign=row["漲跌"],
        change_points=_to_float(row["漲跌點數"]),
        change_percent=_to_float(row["漲跌百分比"]),
    )


def _fetch_raw() -> list[dict]:
    response = requests.get(MI_INDEX_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def fetch_weighted_index() -> IndexQuote:
    """抓取加權指數（大盤）最新收盤資訊。"""
    rows = _fetch_raw()
    for row in rows:
        if row["指數"] == WEIGHTED_INDEX_NAME:
            return _parse_quote(row)
    raise ValueError(f"找不到「{WEIGHTED_INDEX_NAME}」資料，TWSE OpenAPI 格式可能已變更")


def fetch_named_indices(names: list[str]) -> list[IndexQuote]:
    """依指定名稱清單抓取指數，回傳順序與 `names` 一致（找不到的名稱會被略過）。"""
    rows = _fetch_raw()
    quotes_by_name = {row["指數"]: _parse_quote(row) for row in rows}
    return [quotes_by_name[name] for name in names if name in quotes_by_name]


def fetch_sector_indices(top_n: int | None = None) -> list[IndexQuote]:
    """抓取各類股指數（焦點族群），依漲跌幅由高到低排序。

    只保留傳統 27 類股指數（名稱以「類指數」結尾，排除報酬指數變體）。
    """
    rows = _fetch_raw()
    sectors = [
        _parse_quote(row)
        for row in rows
        if row["指數"].endswith("類指數") and "報酬" not in row["指數"]
    ]
    sectors.sort(key=lambda q: q.change_percent, reverse=True)
    if top_n is not None:
        sectors = sectors[:top_n]
    return sectors


def _is_common_stock_code(code: str) -> bool:
    """排除 ETF／ETN（代號以 00 開頭）與非標準 4 位數代號，只保留一般上市股票。"""
    return len(code) == 4 and code.isdigit() and not code.startswith("00")


def _parse_stock_row(row: dict) -> StockQuote | None:
    closing_price = row.get("ClosingPrice", "")
    if not closing_price:
        return None
    close = _to_float(closing_price)
    change_points = _to_float(row.get("Change", "0"))
    prev_close = close - change_points
    change_percent = (change_points / prev_close * 100) if prev_close else 0.0
    return StockQuote(
        code=row["Code"],
        name=row["Name"],
        close=close,
        change_points=change_points,
        change_percent=change_percent,
        trade_value=_to_float(row.get("TradeValue", "0")),
    )


def _fetch_common_stock_quotes() -> list[StockQuote]:
    response = requests.get(STOCK_DAY_ALL_URL, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    rows = response.json()
    return [
        quote
        for quote in (_parse_stock_row(row) for row in rows)
        if quote is not None and _is_common_stock_code(quote.code)
    ]


def fetch_top_stocks_by_value(top_n: int = 60) -> list[StockQuote]:
    """抓取全市場個股當日實際收盤行情，依成交金額（流動性）排序，排除 ETF。

    這份資料用來讓 AI 選股時有「真實股價」可以參考，避免憑訓練記憶編造不符實際
    價格量級的進場區間／防守價。
    """
    quotes = _fetch_common_stock_quotes()
    quotes.sort(key=lambda q: q.trade_value, reverse=True)
    return quotes[:top_n]


def fetch_top_gainers(top_n: int = 30) -> list[StockQuote]:
    """抓取當日漲幅最高的個股（排除 ETF），作為「爆發股」候選池。

    已經在短時間內出現大幅漲勢的個股，比大型權值股更有可能延續動能，
    用來讓 AI 挑選有機會續強的爆發股時有真實價格與動能依據可參考。
    """
    quotes = _fetch_common_stock_quotes()
    quotes.sort(key=lambda q: q.change_percent, reverse=True)
    return quotes[:top_n]
