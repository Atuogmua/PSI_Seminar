"""Tests for the search orchestrator."""

import time
from unittest.mock import patch, MagicMock

import pytest

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.services.search import search_all

FIXED_TS = "2026-10-05T12:00:00+00:00"


def _make_result(shop_name: str, price: float = 100.0) -> BookResult:
    return BookResult(
        id=None,
        isbn=None,
        title=f"Book from {shop_name}",
        author="Author",
        price=price,
        currency="MDL",
        source_url=f"https://{shop_name.lower()}.md/book",
        shop_name=shop_name,
        session_id=0,
        scraped_at=FIXED_TS,
    )


def _mock_scraper(shop_name: str, results: list[BookResult] | None = None, raises: bool = False, block_event=None):
    """Create a mock scraper class.

    Args:
        block_event: if provided, the scraper blocks until this threading.Event is set.
    """
    class MockScraper:
        SHOP_NAME = shop_name
        def search_by_title_or_author(self, query):
            if block_event is not None:
                block_event.wait()
            if raises:
                raise ConnectionError(f"{shop_name} is down")
            return results if results is not None else [_make_result(shop_name)]
    return MockScraper


class TestSearchAllSuccess:
    @patch("book_comparator.services.search.Database")
    @patch("book_comparator.services.search.ALL_SCRAPERS")
    def test_search_all_shops_success(self, mock_scrapers_list, mock_db_cls):
        mock_db = MagicMock()
        mock_db.save_session.return_value = 1
        mock_db_cls.return_value = mock_db

        mock_scrapers_list.__iter__ = lambda self: iter([
            _mock_scraper("Librarius"),
            _mock_scraper("Carturesti"),
            _mock_scraper("Biblion"),
            _mock_scraper("CarteaMea"),
            _mock_scraper("Bookzone"),
        ])

        results, session, failed = search_all("test", "title_author")
        assert len(results) == 5
        assert failed == 0
        assert session.query == "test"
        mock_db.save_results.assert_called_once()


class TestSearchPartialFailure:
    @patch("book_comparator.services.search.Database")
    @patch("book_comparator.services.search.ALL_SCRAPERS")
    def test_search_partial_failure(self, mock_scrapers_list, mock_db_cls):
        mock_db = MagicMock()
        mock_db.save_session.return_value = 1
        mock_db_cls.return_value = mock_db

        mock_scrapers_list.__iter__ = lambda self: iter([
            _mock_scraper("Librarius"),
            _mock_scraper("Carturesti", raises=True),
            _mock_scraper("Biblion"),
            _mock_scraper("CarteaMea", raises=True),
            _mock_scraper("Bookzone"),
        ])

        results, session, failed = search_all("test", "title_author")
        assert len(results) == 3
        assert failed == 2


class TestSearchAllFail:
    @patch("book_comparator.services.search.Database")
    @patch("book_comparator.services.search.ALL_SCRAPERS")
    def test_search_all_fail(self, mock_scrapers_list, mock_db_cls):
        mock_db = MagicMock()
        mock_db.save_session.return_value = 1
        mock_db_cls.return_value = mock_db

        mock_scrapers_list.__iter__ = lambda self: iter([
            _mock_scraper("Librarius", raises=True),
            _mock_scraper("Carturesti", raises=True),
            _mock_scraper("Biblion", raises=True),
            _mock_scraper("CarteaMea", raises=True),
            _mock_scraper("Bookzone", raises=True),
        ])

        results, session, failed = search_all("test", "title_author")
        assert results == []
        assert failed == 5


class TestSearchTimeout:
    @patch("book_comparator.services.search.Database")
    @patch("book_comparator.services.search.ALL_SCRAPERS")
    @patch("book_comparator.services.search.SCRAPER_TIMEOUT", 3)
    def test_search_timeout(self, mock_scrapers_list, mock_db_cls):
        import threading
        block = threading.Event()

        mock_db = MagicMock()
        mock_db.save_session.return_value = 1
        mock_db_cls.return_value = mock_db

        mock_scrapers_list.__iter__ = lambda self: iter([
            _mock_scraper("Librarius"),
            _mock_scraper("Carturesti"),
            _mock_scraper("Biblion"),
            _mock_scraper("CarteaMea"),
            _mock_scraper("SlowShop", block_event=block),
        ])

        start = time.time()
        results, session, failed = search_all("test", "title_author")
        elapsed = time.time() - start

        block.set()  # unblock the stuck thread so it can exit

        assert len(results) == 4
        assert failed == 1
        assert elapsed < 10
