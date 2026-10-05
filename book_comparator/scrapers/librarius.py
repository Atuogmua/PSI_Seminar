"""Scraper for librarius.md bookstore."""

from decimal import Decimal, InvalidOperation

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseScraper


class LibrariusScraper(BaseScraper):
    """Scraper implementation for librarius.md."""

    BASE_URL = "https://www.librarius.md"
    SHOP_NAME = "Librarius"

    def _parse_results(self, soup) -> list[BookResult]:
        """Parse search results page into BookResult objects."""
        results: list[BookResult] = []
        products = soup.select("div.product-item, div.product-card, li.product")

        for product in products:
            try:
                title_el = product.select_one("h3 a, h2 a, .product-title a, .name a")
                price_el = product.select_one(".price, .product-price, .special-price")
                author_el = product.select_one(".author, .product-author, .manufacturer")
                link_el = product.select_one("a[href]")

                if not title_el or not price_el:
                    continue

                title = title_el.get_text(strip=True)
                raw_price = price_el.get_text(strip=True)
                price_clean = raw_price.replace("MDL", "").replace("lei", "").replace(" ", "").replace(",", ".").strip()
                try:
                    price = Decimal(price_clean)
                except InvalidOperation:
                    continue

                author = author_el.get_text(strip=True) if author_el else ""
                href = link_el["href"] if link_el else ""
                source_url = href if href.startswith("http") else f"{self.BASE_URL}{href}"

                results.append(BookResult(
                    isbn="",
                    title=title,
                    author=author,
                    price=price,
                    currency="MDL",
                    source_url=source_url,
                    shop_name=self.SHOP_NAME,
                ))
            except Exception:
                continue

        return results

    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        """Search Librarius by ISBN."""
        soup = self._get_soup(f"{self.BASE_URL}/search", params={"q": isbn})
        results = self._parse_results(soup)
        for r in results:
            r.isbn = isbn
        return results

    def search_by_title(self, title: str) -> list[BookResult]:
        """Search Librarius by book title."""
        soup = self._get_soup(f"{self.BASE_URL}/search", params={"q": title})
        return self._parse_results(soup)

    def search_by_author(self, author: str) -> list[BookResult]:
        """Search Librarius by author name."""
        soup = self._get_soup(f"{self.BASE_URL}/search", params={"q": author})
        return self._parse_results(soup)
