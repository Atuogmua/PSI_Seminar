"""Scraper for carturesti.md bookstore."""

import logging
from urllib.parse import quote

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class CarturestiScraper(BaseBookScraper):
    """Scraper implementation for carturesti.md.

    Uses path-based search: https://carturesti.md/search/{query}
    Handles both original and discounted prices — always takes the final/discounted price.
    """

    SHOP_NAME = "Carturesti"
    BASE_URL = "https://carturesti.md"
    SEARCH_URL = "https://carturesti.md/search/"

    def _parse_results(self, query: str) -> list[BookResult]:
        """Fetch search results and parse the product grid."""
        results: list[BookResult] = []
        try:
            url = f"{self.SEARCH_URL}{quote(query)}"
            soup = self._get(url)
        except Exception as e:
            logger.error("[%s] Request failed: %s", self.SHOP_NAME, e)
            return results

        products = soup.select("div.product-item, div.grid-item, li.product, div.product, div.card")

        for product in products:
            title: str | None = None
            author: str | None = None
            price: float | None = None
            isbn: str | None = None
            source_url: str = ""

            try:
                title_el = product.select_one("h3 a, h2 a, .product-title a, .title a, .name a")
                title = title_el.get_text(strip=True) if title_el else None
            except Exception:
                pass

            try:
                author_el = product.select_one(".author, .product-author, .subtitle")
                author = author_el.get_text(strip=True) if author_el else None
            except Exception:
                pass

            try:
                discount_el = product.select_one(".special-price, .price-new, .discounted-price, .current-price")
                regular_el = product.select_one(".price, .product-price, .regular-price")
                price_el = discount_el or regular_el
                if price_el:
                    price = self.normalize_price(price_el.get_text())
            except Exception:
                pass

            try:
                link_el = product.select_one("a[href]")
                if link_el:
                    href = link_el.get("href", "")
                    source_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            except Exception:
                pass

            try:
                isbn_el = product.select_one(".isbn, [data-isbn]")
                if isbn_el:
                    raw_isbn = isbn_el.get("data-isbn") or isbn_el.get_text()
                    isbn = self.normalize_isbn(raw_isbn)
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

        return results

    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        """Search Carturesti by ISBN."""
        results = self._parse_results(isbn)
        for r in results:
            if r.isbn is None:
                r.isbn = self.normalize_isbn(isbn)
        return results

    def search_by_title(self, title: str) -> list[BookResult]:
        """Search Carturesti by book title."""
        return self._parse_results(title)

    def search_by_author(self, author: str) -> list[BookResult]:
        """Search Carturesti by author name."""
        return self._parse_results(author)
