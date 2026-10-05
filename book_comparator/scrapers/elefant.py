"""Scraper for elefant.md bookstore (INTERSHOP)."""

import re
import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class ElefantScraper(BaseBookScraper):
    """Scraper implementation for elefant.md.

    INTERSHOP Commerce platform. Searches via /filter?SearchTerm={query}.
    Search results contain product-list-item divs with links to detail pages.
    Product tiles are lazy-loaded via JS, so we extract URLs from
    a.product-list-item__sold-out-wrapper and scrape detail pages.
    Detail pages have product title in h1, price in structured elements,
    and ISBN/author in the product specifications section.

    Note: elefant.md may block automated requests; this scraper will
    gracefully return empty results if access is denied.
    """

    SHOP_NAME = "Elefant"
    BASE_URL = "https://www.elefant.md"
    SEARCH_URL = "https://www.elefant.md/filter"

    def _extract_product_links(self, soup) -> list[str]:
        links: list[str] = []
        for a_tag in soup.select("a.product-list-item__sold-out-wrapper"):
            href = a_tag.get("href", "")
            if href and href not in links:
                if not href.startswith("http"):
                    href = f"{self.BASE_URL}{href}"
                links.append(href)
        if not links:
            for div in soup.select("div.product-list-item"):
                a_tag = div.select_one("a[href]")
                if a_tag:
                    href = a_tag.get("href", "")
                    if href and href not in links:
                        if not href.startswith("http"):
                            href = f"{self.BASE_URL}{href}"
                        links.append(href)
        return links

    def _parse_detail_page(self, url: str) -> BookResult | None:
        soup = self._get(url)
        if soup is None:
            return None

        title: str | None = None
        author: str | None = None
        price: float | None = None
        isbn: str | None = None

        try:
            el = soup.select_one("h1")
            if el:
                title = el.get_text(strip=True)
        except Exception:
            pass

        try:
            for a_tag in soup.select("a[href*='/filters/autor-']"):
                author = a_tag.get_text(strip=True)
                break
        except Exception:
            pass

        try:
            text = soup.get_text()
            m = re.search(r"ISBN[:\s]*([\d\-]{10,17})", text)
            if m:
                isbn = self.normalize_isbn(m.group(1))
        except Exception:
            pass

        try:
            for el in soup.select("span.product-new-price, span.current-price, div.price"):
                price = self.normalize_price(el.get_text())
                if price is not None:
                    break
        except Exception:
            pass

        if price is None:
            try:
                text = soup.get_text()
                m = re.search(r"(\d[\d\s,.]*)\s*lei", text)
                if m:
                    price = self.normalize_price(m.group(1))
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
        soup = self._get(self.SEARCH_URL, params={"SearchTerm": query})
        if soup is None:
            return results

        for link in self._extract_product_links(soup):
            result = self._parse_detail_page(link)
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

    def search_by_title(self, title: str) -> list[BookResult]:
        return self._parse_results(title)

    def search_by_author(self, author: str) -> list[BookResult]:
        return self._parse_results(author)
