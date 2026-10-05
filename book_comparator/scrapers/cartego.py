"""Scraper for cartego.md bookstore (WooCommerce REST API)."""

import re
import logging
import time

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class CartegoScraper(BaseBookScraper):
    """Scraper implementation for cartego.md.

    WooCommerce site with Elementor frontend. Standard HTML search doesn't
    render product listings (loaded via JS), so we use the WooCommerce Store
    REST API at /wp-json/wc/store/v1/products?search={query}.
    Product detail pages follow /magazin/librarie/{slug}/ pattern.
    """

    SHOP_NAME = "Cartego"
    BASE_URL = "https://cartego.md"
    API_URL = "https://cartego.md/wp-json/wc/store/v1/products"

    def _search_api(self, query: str) -> list[dict]:
        logger.debug("[%s] GET %s params={search: %s}", self.SHOP_NAME, self.API_URL, query)
        try:
            resp = self.session.get(
                self.API_URL,
                params={"search": query, "per_page": 20},
                timeout=10,
            )
            self._last_request_time = time.time()
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("[%s] API failed: %s", self.SHOP_NAME, exc)
            return []

    def _parse_results(self, query: str) -> list[BookResult]:
        results: list[BookResult] = []
        items = self._search_api(query)

        for item in items:
            title = item.get("name", "")
            if not title:
                continue

            permalink = item.get("permalink", "")
            prices = item.get("prices", {})
            raw_price = prices.get("price", "")
            price: float | None = None
            if raw_price:
                try:
                    price = int(raw_price) / 100.0
                except (ValueError, TypeError):
                    price = self.normalize_price(str(raw_price))

            isbn: str | None = None
            author: str | None = None

            description = item.get("short_description", "") + " " + item.get("description", "")
            m = re.search(r"ISBN[:\s]*([\d\-]{10,17})", description)
            if m:
                isbn = self.normalize_isbn(m.group(1))

            if not isbn or not author:
                soup = self._get(permalink) if permalink else None
                if soup:
                    try:
                        text = soup.get_text()
                        if not isbn:
                            m = re.search(r"ISBN[:\s]*([\d\-]{10,17})", text)
                            if m:
                                isbn = self.normalize_isbn(m.group(1))
                        if not author:
                            m = re.search(r"Autor[:\s]*(.+?)(?:\n|ISBN|Editura|$)", text)
                            if m:
                                author = m.group(1).strip()
                    except Exception:
                        pass

            results.append(BookResult(
                id=None,
                isbn=isbn,
                title=title,
                author=author,
                price=price,
                currency="MDL",
                source_url=permalink or f"{self.BASE_URL}/?p={item.get('id', '')}",
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
