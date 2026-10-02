from unittest.mock import patch

from stock_bot.fetchers import news


class FakeEntry(dict):
    """模擬 feedparser 的 FeedParserDict：支援屬性與 .get() 兩種存取方式。"""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc


def _fake_feed(entries):
    feed = FakeEntry(entries=entries)
    return feed


@patch("stock_bot.fetchers.news.feedparser.parse")
def test_fetch_news_parses_entries(mock_parse):
    mock_parse.return_value = _fake_feed(
        [
            FakeEntry(
                title="台股大漲創新高",
                link="https://example.com/a",
                published="Fri, 02 Oct 2026 08:00:00 GMT",
                source=FakeEntry(title="鉅亨網"),
            ),
            FakeEntry(
                title="無來源新聞",
                link="https://example.com/b",
                published="",
            ),
        ]
    )

    items = news.fetch_news(query="台股 大盤", limit=10)

    assert len(items) == 2
    assert items[0].title == "台股大漲創新高"
    assert items[0].source == "鉅亨網"
    assert items[1].source == ""


@patch("stock_bot.fetchers.news.feedparser.parse")
def test_fetch_news_respects_limit(mock_parse):
    mock_parse.return_value = _fake_feed(
        [
            FakeEntry(title=f"新聞 {i}", link=f"https://example.com/{i}", published="")
            for i in range(5)
        ]
    )

    items = news.fetch_news(limit=2)

    assert len(items) == 2
