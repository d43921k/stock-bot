"""抓取台灣證券交易所（TWSE）OpenAPI 的大盤指數與類股指數資料。

資料來源：https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX
（公開資料，不需要 API Key）
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

MI_INDEX_URL = "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX"
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
