"""Scraper for carturesti.md bookstore."""

import logging
import time

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class CarturestiScraper(BaseBookScraper):
    """Scraper implementation for carturesti.md.

    Uses a CSRF-protected AJAX search API (POST /product/simple-search).
    Fetches any page first to obtain the CSRF token and session cookies,
    then follows product links to /carte/{slug} detail pages.
    Extracts title from h1.titluProdus, author from div.autorProdus,
    price from span.pret + span.bani, and ISBN from div.productAttr rows.
    """

    SHOP_NAME = "Carturesti"
    BASE_URL = "https://carturesti.md"
    SEARCH_URL = "https://carturesti.md/search/"
    SEARCH_API = "https://carturesti.md/product/simple-search"

    def _ensure_csrf(self) -> str | None:
        """GET the homepage to obtain CSRF token and session cookies."""
        try:
            logger.debug("[%s] Fetching CSRF token", self.SHOP_NAME)
            resp = self.session.get(self.BASE_URL, timeout=10)
            self._last_request_time = time.time()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "lxml")
            meta = soup.select_one('meta[name="csrf-token"]')
            if meta:
                return meta["content"]
        except Exception as exc:
            logger.warning("[%s] CSRF fetch failed: %s", self.SHOP_NAME, exc)
        return None

    def _search_api(self, query: str) -> list[dict]:
        """Call the AJAX search API and return the list of product entries."""
        csrf = self._ensure_csrf()
        if not csrf:
            return []

        try:
            logger.debug("[%s] POST %s term=%s", self.SHOP_NAME, self.SEARCH_API, query)
            resp = self.session.post(
                self.SEARCH_API,
                data={"_csrf": csrf, "term": query, "perpage": 10},
                headers={"X-Requested-With": "XMLHttpRequest"},
                timeout=10,
            )
            self._last_request_time = time.time()
            resp.raise_for_status()
            data = resp.json()
            items = []
            for key, val in data.items():
                if isinstance(val, dict) and "url" in val:
                    items.append(val)
            return items
        except Exception as exc:
            logger.warning("[%s] Search API failed: %s", self.SHOP_NAME, exc)
            return []

    def _parse_detail_page(self, url: str) -> BookResult | None:
        """Parse a product detail page."""
        soup = self._get(url)
        if soup is None:
            return None

        title: str | None = None
        author: str | None = None
        price: float | None = None
        isbn: str | None = None

        try:
            el = soup.select_one("h1.titluProdus")
            if el:
                title = el.get_text(strip=True)
        except Exception:
            pass

        try:
            el = soup.select_one("div.autorProdus")
            if el:
                author = el.get_text(strip=True)
        except Exception:
            pass

        try:
            pret_el = soup.select_one("span.pret")
            if pret_el:
                bani_el = pret_el.select_one("span.bani")
                bani_text = bani_el.get_text(strip=True) if bani_el else ""
                full_text = pret_el.get_text(strip=True)
                if bani_text:
                    integer_part = full_text.replace(bani_text, "").strip()
                    combined = f"{integer_part}{bani_text}"
                else:
                    combined = full_text
                price = self.normalize_price(combined)
        except Exception:
            pass

        try:
            details = soup.select_one("div.row.detailsContainer")
            if details:
                for attr_div in details.select("div.productAttr"):
                    label_el = attr_div.select_one("span.productAttrLabel")
                    if not label_el:
                        continue
                    label = label_el.get_text(strip=True).lower()
                    full = attr_div.get_text(strip=True)
                    value = full.replace(label_el.get_text(strip=True), "").strip()
                    if "isbn" in label:
                        isbn = self.normalize_isbn(value)
        except Exception:
            pass

        if not title:
            return None

        return BookResult(
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
        )

    def _parse_results(self, query: str) -> list[BookResult]:
        results: list[BookResult] = []
        items = self._search_api(query)

        for item in items:
            rel_url = item.get("url", "")
            if "?" in rel_url:
                rel_url = rel_url.split("?")[0]
            url = f"{self.BASE_URL}{rel_url}" if rel_url else ""

            if not url:
                continue

            result = self._parse_detail_page(url)
            if result:
                results.append(result)

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
