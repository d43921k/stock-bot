"""抓取美股大盤指數（透過 Yahoo Finance Chart API，免 API Key）。"""

from __future__ import annotations

from dataclasses import dataclass

import requests

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
REQUEST_TIMEOUT = 10
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}

# Yahoo Finance 代碼 -> 顯示名稱
US_INDEX_SYMBOLS = {
    "^DJI": "道瓊工業指數",
    "^GSPC": "S&P 500",
    "^IXIC": "那斯達克綜合指數",
}


@dataclass(frozen=True)
class IndexQuote:
    name: str
    close: float
    change_points: float
    change_percent: float

    @property
    def change_sign(self) -> str:
        if self.change_points > 0:
            return "+"
        if self.change_points < 0:
            return "-"
        return ""

    @property
    def is_up(self) -> bool:
        return self.change_points > 0

    @property
    def is_down(self) -> bool:
        return self.change_points < 0


def _fetch_one(symbol: str, name: str) -> IndexQuote:
    response = requests.get(
        YAHOO_CHART_URL.format(symbol=symbol),
        params={"interval": "1d", "range": "5d"},
        headers=REQUEST_HEADERS,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    meta = response.json()["chart"]["result"][0]["meta"]
    # 用 fulldayChange／regularMarketChangePercent 這組 Yahoo 自己算好、互相一致的數字，
    # 不要用 close - chartPreviousClose 計算點數——chartPreviousClose 在某些時段
    # （例如非交易時間、range=5d 的邊界）會對應到不同天的收盤價，跟漲跌百分比的基準不一致，
    # 導致算出來的漲跌方向跟 Yahoo 自己回報的漲跌百分比方向相反。
    return IndexQuote(
        name=name,
        close=float(meta["regularMarketPrice"]),
        change_points=float(meta["fulldayChange"]),
        change_percent=float(meta["regularMarketChangePercent"]),
    )


def fetch_us_indices() -> list[IndexQuote]:
    """抓取道瓊、S&P 500、那斯達克綜合指數的最新收盤資訊。"""
    return [_fetch_one(symbol, name) for symbol, name in US_INDEX_SYMBOLS.items()]
