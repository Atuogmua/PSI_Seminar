"""Scraper for dorinta.md bookstore (custom platform)."""

import re
import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class DorintaScraper(BaseBookScraper):
    """Scraper implementation for dorinta.md.

    Custom platform. Searches via /ro/catalog/search?keyword={query}.
    Product cards are div.prd-teaser with h3.prd-title > a for links,
    and div.price-new for prices.
    Detail pages have product specs as inline text (ISBN, Autor, Editura).
    """

    SHOP_NAME = "Dorinta"
    BASE_URL = "https://dorinta.md"
    SEARCH_URL = "https://dorinta.md/ro/catalog/search"

    def _extract_product_links(self, soup) -> list[tuple[str, str | None, float | None]]:
        items: list[tuple[str, str | None, float | None]] = []
        for card in soup.select("div.prd-teaser"):
            a_tag = card.select_one("h3.prd-title a")
            if not a_tag or not a_tag.get("href"):
                continue
            url = a_tag["href"]
            title = a_tag.get_text(strip=True) or None

            price: float | None = None
            price_el = card.select_one("div.price-new")
            if price_el:
                price = self.normalize_price(price_el.get_text())

            items.append((url, title, price))
        return items

    def _parse_detail_page(self, url: str) -> dict:
        info: dict = {}
        soup = self._get(url)
        if soup is None:
            return info

        try:
            el = soup.select_one("h1") or soup.select_one("h2")
            if el:
                info["title"] = el.get_text(strip=True)
        except Exception:
            pass

        try:
            text = soup.get_text()
            m = re.search(r"ISBN\s*:\s*([\d\-]{10,17})", text)
            if m:
                info["isbn"] = self.normalize_isbn(m.group(1))
        except Exception:
            pass

        try:
            text = soup.get_text()
            m = re.search(r"Autor\s*:\s*(.+?)(?:\n|ISBN|Editura|Categorie|Tip|Dimensiune|Nr|$)", text)
            if m:
                info["author"] = m.group(1).strip()
        except Exception:
            pass

        try:
            price_el = soup.select_one("div.price-new")
            if price_el:
                info["price"] = self.normalize_price(price_el.get_text())
        except Exception:
            pass

        return info

    def _parse_results(self, query: str) -> list[BookResult]:
        results: list[BookResult] = []
        soup = self._get(self.SEARCH_URL, params={"keyword": query})
        if soup is None:
            return results

        items = self._extract_product_links(soup)
        for url, list_title, list_price in items:
            detail = self._parse_detail_page(url)
            title = detail.get("title", list_title)
            if not title:
                continue

            results.append(BookResult(
                id=None,
                isbn=detail.get("isbn"),
                title=title,
                author=detail.get("author"),
                price=detail.get("price", list_price),
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
