"""Scraper for mesageria.md bookstore (custom JSP platform)."""

import re
import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class MesageriaScraper(BaseBookScraper):
    """Scraper implementation for mesageria.md.

    Custom Java/JSP platform. Catalog browsing via /catalog/carte.jsp,
    search via /catalog/search/{query}.jsp.
    Product cards are div.produss containing div.productRightContent with:
      - div.title_produs > a for title and link
      - div.author for author
      - Inline bold-label metadata: <b>ISBN:</b>, <b>Editura:</b>, <b>Preț:</b>
    Detail pages at /single/carte/{category}/{slug}.
    """

    SHOP_NAME = "Mesageria"
    BASE_URL = "https://mesageria.md"

    def _search_url(self, query: str) -> str:
        return f"{self.BASE_URL}/catalog/search/{query}.jsp"

    def _parse_results(self, query: str) -> list[BookResult]:
        results: list[BookResult] = []
        soup = self._get(self._search_url(query))
        if soup is None:
            return results

        for card in soup.select("div.produss"):
            content = card.select_one("div.productRightContent")
            if not content:
                continue

            title: str | None = None
            author: str | None = None
            price: float | None = None
            isbn: str | None = None
            url: str = ""

            try:
                title_el = content.select_one("div.title_produs a")
                if title_el:
                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if href:
                        url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
            except Exception:
                pass

            try:
                author_el = content.select_one("div.author")
                if author_el:
                    raw = author_el.get_text(strip=True)
                    author = re.sub(r"^de\s+", "", raw).strip() or None
            except Exception:
                pass

            try:
                text = content.decode_contents()
                m = re.search(r"<b>ISBN:</b>\s*([\d\-]+)", text)
                if m:
                    isbn = self.normalize_isbn(m.group(1))
            except Exception:
                pass

            try:
                text = content.decode_contents()
                m = re.search(r"<b>Preț:</b>\s*([\d.,]+)\s*MDL", text)
                if m:
                    price = self.normalize_price(m.group(1))
            except Exception:
                pass

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

    def search_by_title(self, title: str) -> list[BookResult]:
        return self._parse_results(title)

    def search_by_author(self, author: str) -> list[BookResult]:
        return self._parse_results(author)
