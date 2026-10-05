"""Scraper for biblion.md bookstore."""

from decimal import Decimal, InvalidOperation

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseScraper


class BiblionScraper(BaseScraper):
    """Scraper implementation for biblion.md."""

    BASE_URL = "https://www.biblion.md"
    SHOP_NAME = "Biblion"

    def _parse_results(self, soup) -> list[BookResult]:
        """Parse search results page into BookResult objects."""
        results: list[BookResult] = []
        products = soup.select("div.product-item, div.product-card, li.product, div.product-layout")

        for product in products:
            try:
                title_el = product.select_one("h4 a, h3 a, .product-title a, .name a, .caption a")
                price_el = product.select_one(".price, .product-price, .price-new, .special-price")
                author_el = product.select_one(".author, .product-author, .description")
                link_el = product.select_one("a[href]")

                if not title_el or not price_el:
                    continue

                title = title_el.get_text(strip=True)
                raw_price = price_el.get_text(strip=True)
                price_clean = raw_price.replace("MDL", "").replace("lei", "").replace("L", "").replace(" ", "").replace(",", ".").strip()
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
        """Search Biblion by ISBN."""
        soup = self._get_soup(f"{self.BASE_URL}/index.php", params={"route": "product/search", "search": isbn})
        results = self._parse_results(soup)
        for r in results:
            r.isbn = isbn
        return results

    def search_by_title(self, title: str) -> list[BookResult]:
        """Search Biblion by book title."""
        soup = self._get_soup(f"{self.BASE_URL}/index.php", params={"route": "product/search", "search": title})
        return self._parse_results(soup)

    def search_by_author(self, author: str) -> list[BookResult]:
        """Search Biblion by author name."""
        soup = self._get_soup(f"{self.BASE_URL}/index.php", params={"route": "product/search", "search": author})
        return self._parse_results(soup)
