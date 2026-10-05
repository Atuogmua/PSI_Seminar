"""Scraper for bookstore.md (Bitrix CMS)."""

import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class BookstoreMdScraper(BaseBookScraper):
    """Scraper implementation for bookstore.md.

    Bitrix-based site. Searches via /catalog/?q={query}.
    Product cards are div.item with a.title linking to /catalog/{cat}/{id}/.
    Price shown as p.price with "NNN Lei" format.
    Detail pages have h1.title, ul.specifications li.itm for metadata,
    and p.price for price.
    """

    SHOP_NAME = "BookStore"
    BASE_URL = "https://bookstore.md"
    SEARCH_URL = "https://bookstore.md/catalog/"

    def _extract_product_links(self, soup) -> list[str]:
        links: list[str] = []
        for a_tag in soup.select("a.title"):
            href = a_tag.get("href", "")
            if href and "/catalog/" in href:
                if not href.startswith("http"):
                    href = f"{self.BASE_URL}{href}"
                if href not in links:
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
            el = soup.select_one("h1.title")
            if not el:
                el = soup.select_one("h1")
            if el:
                title = el.get_text(strip=True)
        except Exception:
            pass

        try:
            for li in soup.select("ul.specifications li.itm"):
                ps = li.select("p.font-md")
                if len(ps) >= 2:
                    label = ps[0].get_text(strip=True).lower()
                    value = ps[1].get_text(strip=True)
                    if "cod" in label or "isbn" in label:
                        isbn = self.normalize_isbn(value)
                    elif "autor" in label or "author" in label:
                        a_tag = ps[1].select_one("a")
                        author = a_tag.get_text(strip=True) if a_tag else value
        except Exception:
            pass

        try:
            el = soup.select_one("p.price")
            if el:
                price = self.normalize_price(el.get_text())
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
        soup = self._get(self.SEARCH_URL, params={"q": query})
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

    def search_by_title_or_author(self, query: str) -> list[BookResult]:
        return self._parse_results(query)
