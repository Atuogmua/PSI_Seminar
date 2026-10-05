"""Scraper for librarius.md bookstore."""

import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class LibrariusScraper(BaseBookScraper):
    """Scraper implementation for librarius.md.

    Uses the JSON autocomplete API /ajax/search-drawer-suggest for search,
    then follows product links to /ro/bookitem/{id} detail pages.
    Extracts ISBN and full metadata from div.product-page-props-box.
    """

    SHOP_NAME = "Librarius"
    BASE_URL = "https://librarius.md"
    SEARCH_URL = "https://librarius.md/ro/search"
    SUGGEST_URL = "https://librarius.md/ajax/search-drawer-suggest"

    def _search_api(self, query: str) -> list[dict]:
        """Call the JSON suggest API and return the suggestions list."""
        logger.debug("[%s] GET %s params={search: %s}", self.SHOP_NAME, self.SUGGEST_URL, query)
        try:
            resp = self.session.get(self.SUGGEST_URL, params={"search": query}, timeout=10)
            self._last_request_time = __import__("time").time()
            resp.raise_for_status()
            data = resp.json()
            return data.get("suggestions", [])
        except Exception as exc:
            logger.warning("[%s] Suggest API failed: %s", self.SHOP_NAME, exc)
            return []

    def _parse_detail_page(self, url: str) -> dict:
        """Parse a product detail page for ISBN and other props."""
        info: dict = {}
        soup = self._get(url)
        if soup is None:
            return info

        try:
            el = soup.select_one("div.product-title-page")
            if el:
                info["title"] = el.get_text(strip=True)
        except Exception:
            pass

        try:
            props_box = soup.select_one("div.product-page-props-box")
            if props_box:
                for row in props_box.select("div.row.book-props-item"):
                    name_el = row.select_one("div.book-prop-name")
                    value_el = row.select_one("div.book-prop-value")
                    if not name_el or not value_el:
                        continue
                    label = name_el.get_text(strip=True).lower()
                    value = value_el.get_text(strip=True)
                    if "autor" in label:
                        info["author"] = value
                    elif "isbn" in label:
                        info["isbn"] = self.normalize_isbn(value)
        except Exception:
            pass

        try:
            btn = soup.select_one("button#addToCartButton")
            if btn and btn.get("data-price"):
                info["price"] = self.normalize_price(btn["data-price"])
        except Exception:
            pass

        if "price" not in info:
            try:
                el = soup.select_one("div.product-book-price__actual")
                if el:
                    info["price"] = self.normalize_price(el.get_text())
            except Exception:
                pass

        return info

    def _parse_results(self, query: str) -> list[BookResult]:
        results: list[BookResult] = []
        suggestions = self._search_api(query)

        for item in suggestions:
            if item.get("type") != "book":
                continue

            title = item.get("title")
            author = item.get("subtitle") or None
            price_raw = item.get("price")
            price = self.normalize_price(str(price_raw)) if price_raw else None
            url = item.get("url", "")
            if url and not url.startswith("http"):
                url = f"{self.BASE_URL}{url}"

            isbn: str | None = None
            if url:
                detail = self._parse_detail_page(url)
                isbn = detail.get("isbn")
                if not author and detail.get("author"):
                    author = detail["author"]
                if price is None and detail.get("price") is not None:
                    price = detail["price"]
                if not title and detail.get("title"):
                    title = detail["title"]

            if not title:
                continue

            results.append(BookResult(
                id=None,
                isbn=isbn,
                title=title,
                author=author,
                price=price,
                currency="MDL",
                source_url=url,
                shop_name=self.SHOP_NAME,
                session_id=0,
                scraped_at=self._now_iso(),
            ))

        logger.info("[%s] Found %d results", self.SHOP_NAME, len(results))
        return results

    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        results = self._parse_results(isbn)
        for r in results:
            if r.isbn is None:
                r.isbn = self.normalize_isbn(isbn)
        return results

    def search_by_title_or_author(self, query: str) -> list[BookResult]:
        return self._parse_results(query)
