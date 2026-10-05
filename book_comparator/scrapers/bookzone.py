"""Scraper for bookzone.md bookstore."""

import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class BookzoneScraper(BaseBookScraper):
    """Scraper implementation for bookzone.md."""

    SHOP_NAME = "Bookzone"
    BASE_URL = "https://bookzone.md"
    SEARCH_URL = "https://bookzone.md/search"

    def _parse_results(self, query: str) -> list[BookResult]:
        """Fetch search results and parse product cards."""
        results: list[BookResult] = []
        soup = self._get(self.SEARCH_URL, params={"q": query})
        if soup is None:
            return results

        products = soup.select(
            "div.product-item, div.product-card, li.product, "
            "div.product-layout, div.product, div.card"
        )

        for product in products:
            title: str | None = None
            author: str | None = None
            price: float | None = None
            isbn: str | None = None
            source_url: str = ""

            try:
                title_el = product.select_one("h4 a, h3 a, .product-title a, .name a, .title a")
                title = title_el.get_text(strip=True) if title_el else None
            except Exception:
                pass

            try:
                author_el = product.select_one(".author, .product-author, .subtitle")
                author = author_el.get_text(strip=True) if author_el else None
            except Exception:
                pass

            try:
                price_el = product.select_one(".price-new, .special-price, .price, .product-price")
                if price_el:
                    price = self.normalize_price(price_el.get_text())
            except Exception:
                pass

            try:
                link_el = product.select_one("h4 a, h3 a, .product-title a, .name a, a[href]")
                if link_el:
                    href = link_el.get("href", "")
                    source_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            except Exception:
                pass

            try:
                isbn_el = product.select_one(".isbn, [data-isbn]")
                if isbn_el:
                    isbn = self.normalize_isbn(isbn_el.get("data-isbn") or isbn_el.get_text())
            except Exception:
                pass

            if not title or price is None:
                continue

            results.append(BookResult(
                id=None,
                isbn=isbn,
                title=title,
                author=author,
                price=price,
                currency="MDL",
                source_url=source_url,
                shop_name=self.SHOP_NAME,
                session_id=0,
                scraped_at=self._now_iso(),
            ))

        logger.info("[%s] Found %d results", self.SHOP_NAME, len(results))
        return results

    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        """Search Bookzone by ISBN."""
        results = self._parse_results(isbn)
        for r in results:
            if r.isbn is None:
                r.isbn = self.normalize_isbn(isbn)
        return results

    def search_by_title(self, title: str) -> list[BookResult]:
        """Search Bookzone by book title."""
        return self._parse_results(title)

    def search_by_author(self, author: str) -> list[BookResult]:
        """Search Bookzone by author name."""
        return self._parse_results(author)
