"""Scraper for bookzone.md bookstore (Nuxt.js / Vue SSR)."""

import re
import logging
import time

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class BookzoneScraper(BaseBookScraper):
    """Scraper implementation for bookzone.md.

    Nuxt.js (Vue) app with SSR. Uses the JSON API at api.bookzone.md/search
    for search, then follows product links to /carte/{slug} detail pages.
    Detail pages use double-underscore class names (details__title__name, etc.)
    and a product_details section with specs (ISBN, author, publisher, year).
    """

    SHOP_NAME = "Bookzone"
    BASE_URL = "https://bookzone.md"
    SEARCH_URL = "https://bookzone.md/search"
    API_URL = "https://api.bookzone.md"

    def _search_api(self, query: str) -> list[dict]:
        """Call the api.bookzone.md JSON search endpoint."""
        url = f"{self.API_URL}/search"
        logger.debug("[%s] GET %s params={q: %s}", self.SHOP_NAME, url, query)
        try:
            resp = self.session.get(url, params={"q": query}, timeout=10)
            self._last_request_time = time.time()
            resp.raise_for_status()
            data = resp.json()
            return data.get("titles", [])
        except Exception as exc:
            logger.warning("[%s] Search API failed: %s", self.SHOP_NAME, exc)
            return []

    def _parse_detail_page(self, url: str) -> dict:
        """Parse the SSR product detail page for additional fields."""
        info: dict = {}
        soup = self._get(url)
        if soup is None:
            return info

        try:
            el = soup.select_one("h1.details__title__name")
            if el:
                info["title"] = el.get_text(strip=True)
        except Exception:
            pass

        try:
            el = soup.select_one("a.details__title__book")
            if el:
                info["author"] = el.get_text(strip=True)
        except Exception:
            pass

        try:
            el = soup.select_one("span.details__info__price__new")
            if el:
                info["price"] = self.normalize_price(el.get_text())
        except Exception:
            pass

        try:
            for detail in soup.select("div.product_details_detail"):
                top = detail.select_one("div.product_details_detail_top")
                bottom = detail.select_one("div.product_details_detail_bottom")
                if not top or not bottom:
                    continue
                label = top.get_text(strip=True).lower()
                value = bottom.get_text(strip=True)
                if "isbn" in label:
                    info["isbn"] = self.normalize_isbn(value)
                elif "autor" in label:
                    info.setdefault("author", value)
        except Exception:
            pass

        if "isbn" not in info:
            try:
                text = soup.get_text()
                m = re.search(r"ISBN\s*([\d\-]{10,17})", text)
                if m:
                    info["isbn"] = self.normalize_isbn(m.group(1))
            except Exception:
                pass

        return info

    def _parse_results(self, query: str) -> list[BookResult]:
        results: list[BookResult] = []
        titles = self._search_api(query)

        for item in titles:
            slug = item.get("url", "")
            if not slug:
                continue

            page_url = f"{self.BASE_URL}/carte/{slug}"
            title = item.get("title")
            price = item.get("price")
            author: str | None = None
            isbn: str | None = None

            detail = self._parse_detail_page(page_url)
            if detail.get("title"):
                title = detail["title"]
            if detail.get("author"):
                author = detail["author"]
            if detail.get("isbn"):
                isbn = detail["isbn"]
            if detail.get("price") is not None:
                price = detail["price"]
            elif price is not None:
                price = float(price)

            if not title:
                continue

            results.append(BookResult(
                id=None,
                isbn=isbn,
                title=title,
                author=author,
                price=price,
                currency="MDL",
                source_url=page_url,
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
