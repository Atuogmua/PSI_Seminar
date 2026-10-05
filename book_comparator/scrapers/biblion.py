"""Scraper for biblion.md bookstore."""

import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class BiblionScraper(BaseBookScraper):
    """Scraper implementation for biblion.md.

    Follows product links when ISBN is not displayed in the listing.
    """

    SHOP_NAME = "Biblion"
    BASE_URL = "https://biblion.md"
    SEARCH_URL = "https://biblion.md/index.php"

    def _fetch_isbn_from_detail(self, url: str) -> str | None:
        """Follow a product detail page link and attempt to extract ISBN."""
        try:
            soup = self._get(url)
            isbn_el = soup.select_one(".isbn, [itemprop='isbn'], td:contains('ISBN') + td, .product-isbn")
            if isbn_el:
                return self.normalize_isbn(isbn_el.get_text())
            text = soup.get_text()
            import re
            match = re.search(r"ISBN[:\s]*([\d\-]{10,17})", text)
            if match:
                return self.normalize_isbn(match.group(1))
        except Exception:
            pass
        return None

    def _parse_results(self, query: str) -> list[BookResult]:
        """Fetch search results and parse the results list."""
        results: list[BookResult] = []
        try:
            soup = self._get(self.SEARCH_URL, params={"route": "product/search", "search": query})
        except Exception as e:
            logger.error("[%s] Request failed: %s", self.SHOP_NAME, e)
            return results

        products = soup.select("div.product-item, div.product-card, li.product, div.product-layout, div.product-thumb")

        for product in products:
            title: str | None = None
            author: str | None = None
            price: float | None = None
            isbn: str | None = None
            source_url: str = ""

            try:
                title_el = product.select_one("h4 a, h3 a, .product-title a, .name a, .caption a")
                title = title_el.get_text(strip=True) if title_el else None
            except Exception:
                pass

            try:
                author_el = product.select_one(".author, .product-author, .description")
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
                link_el = product.select_one("h4 a, h3 a, .product-title a, .name a, .caption a, a[href]")
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

            if isbn is None and source_url:
                isbn = self._fetch_isbn_from_detail(source_url)

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

    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        """Search Biblion by ISBN."""
        results = self._parse_results(isbn)
        for r in results:
            if r.isbn is None:
                r.isbn = self.normalize_isbn(isbn)
        return results

    def search_by_title(self, title: str) -> list[BookResult]:
        """Search Biblion by book title."""
        return self._parse_results(title)

    def search_by_author(self, author: str) -> list[BookResult]:
        """Search Biblion by author name."""
        return self._parse_results(author)
