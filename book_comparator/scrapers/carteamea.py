"""Scraper for carteamea.md bookstore."""

import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)

MAX_PAGES = 3


class CarteameaScraper(BaseBookScraper):
    """Scraper implementation for carteamea.md.

    Handles pagination — scrapes the first 3 pages of results maximum.
    """

    SHOP_NAME = "CarteaMea"
    BASE_URL = "https://carteamea.md"
    SEARCH_URL = "https://carteamea.md/search"

    def _parse_page(self, soup) -> list[BookResult]:
        """Parse a single page of search results into BookResult objects."""
        results: list[BookResult] = []
        products = soup.select("div.product-item, div.product-card, li.product, div.product-thumb, div.product")

        for product in products:
            title: str | None = None
            author: str | None = None
            price: float | None = None
            isbn: str | None = None
            source_url: str = ""

            try:
                title_el = product.select_one("h4 a, h3 a, .product-title a, .name a, .caption a, .title a")
                title = title_el.get_text(strip=True) if title_el else None
            except Exception:
                pass

            try:
                author_el = product.select_one(".author, .product-author, .description, .subtitle")
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
                isbn=isbn,
                title=title,
                author=author,
                price=price,
                currency="MDL",
                source_url=source_url,
                shop_name=self.SHOP_NAME,
            ))

        return results

    def _parse_results(self, query: str) -> list[BookResult]:
        """Fetch up to MAX_PAGES pages of search results."""
        all_results: list[BookResult] = []

        for page in range(1, MAX_PAGES + 1):
            try:
                soup = self._get(self.SEARCH_URL, params={"q": query, "page": str(page)})
            except Exception as e:
                logger.error("[%s] Request failed on page %d: %s", self.SHOP_NAME, page, e)
                break

            page_results = self._parse_page(soup)
            if not page_results:
                break

            all_results.extend(page_results)

            next_link = soup.select_one("a.next, li.next a, .pagination a[rel='next']")
            if not next_link:
                break

        return all_results

    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        """Search CarteaMea by ISBN."""
        results = self._parse_results(isbn)
        for r in results:
            if r.isbn is None:
                r.isbn = self.normalize_isbn(isbn)
        return results

    def search_by_title(self, title: str) -> list[BookResult]:
        """Search CarteaMea by book title."""
        return self._parse_results(title)

    def search_by_author(self, author: str) -> list[BookResult]:
        """Search CarteaMea by author name."""
        return self._parse_results(author)
