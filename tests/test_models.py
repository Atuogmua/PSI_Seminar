"""Tests for BookResult and SearchSession dataclasses."""

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.scrapers.base import BaseBookScraper


def _make_result(**overrides) -> BookResult:
    """Helper to create a BookResult with sensible defaults."""
    defaults = dict(
        id=None,
        isbn=None,
        title="Test",
        author=None,
        price=None,
        currency="MDL",
        source_url="https://example.com",
        shop_name="TestShop",
        session_id=0,
        scraped_at="2026-10-05T12:00:00+00:00",
    )
    defaults.update(overrides)
    return BookResult(**defaults)


class TestPriceDisplay:
    """Tests for BookResult.price_display()."""

    def test_price_display_with_value(self):
        result = _make_result(price=149.0, currency="MDL")
        assert result.price_display() == "149.00 MDL"

    def test_price_display_none(self):
        result = _make_result(price=None, currency="MDL")
        assert result.price_display() == "N/A"

    def test_price_display_zero(self):
        result = _make_result(price=0.0, currency="MDL")
        assert result.price_display() == "0.00 MDL"

    def test_price_display_decimal_places(self):
        result = _make_result(price=99.5, currency="LEI")
        assert result.price_display() == "99.50 LEI"


class TestIsbnNormalization:
    """Tests for BaseBookScraper.normalize_isbn()."""

    def test_isbn13_with_hyphens(self):
        assert BaseBookScraper.normalize_isbn("978-9975-74-123-4") == "9789975741234"

    def test_isbn10_with_hyphens(self):
        assert BaseBookScraper.normalize_isbn("0-306-40615-2") == "0306406152"

    def test_isbn_too_short(self):
        assert BaseBookScraper.normalize_isbn("123") is None

    def test_isbn_none(self):
        assert BaseBookScraper.normalize_isbn(None) is None

    def test_isbn_empty(self):
        assert BaseBookScraper.normalize_isbn("") is None

    def test_isbn10_with_x(self):
        assert BaseBookScraper.normalize_isbn("0-19-853453-X") == "019853453X"


class TestPriceNormalization:
    """Tests for BaseBookScraper.normalize_price()."""

    def test_mdl_suffix(self):
        assert BaseBookScraper.normalize_price("150,50 MDL") == 150.5

    def test_lei_suffix(self):
        assert BaseBookScraper.normalize_price("89 lei") == 89.0

    def test_invalid_string(self):
        assert BaseBookScraper.normalize_price("abc") is None

    def test_whitespace(self):
        assert BaseBookScraper.normalize_price("  120 ") == 120.0


class TestSearchSession:
    """Tests for SearchSession."""

    def test_create_factory(self):
        session = SearchSession.create("test", "title")
        assert session.id is None
        assert session.query == "test"
        assert session.search_type == "title"
        assert session.timestamp  # non-empty ISO string
