"""Scraper for litera.md bookstore (OpenCart)."""

import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class LiteraScraper(BaseBookScraper):
    """Scraper implementation for litera.md.

    OpenCart-based site. Searches via /cautare?search={query}.
    Product cards use div.product-thumb with links in h4 > a.
    Detail pages expose ISBN, author, price in ul.product-params (span.pl / span.pt)
    and price in li.special inside div.buy-box.
    """

    SHOP_NAME = "Litera"
    BASE_URL = "https://litera.md"
    SEARCH_URL = "https://litera.md/cautare"

    def _parse_detail_page(self, url: str) -> BookResult | None:
        soup = self._get(url)
        if soup is None:
            return None

        title: str | None = None
        author: str | None = None
        price: float | None = None
        isbn: str | None = None

        try:
            el = soup.select_one("h1.heading-title")
            if el:
                title = el.get_text(strip=True)
        except Exception:
            pass

        try:
            for li in soup.select("ul.product-params li"):
                label_el = li.select_one("span.pl")
                value_el = li.select_one("span.pt")
                if not label_el:
                    continue
                label = label_el.get_text(strip=True).lower()
                if "isbn" in label and value_el:
                    isbn = self.normalize_isbn(value_el.get_text(strip=True))
                elif ("autor" in label or "author" in label) and value_el:
                    author = value_el.get_text(strip=True)
                if not author:
                    a_tag = li.select_one("a")
                    if a_tag and label_el and "autor" in label_el.get_text(strip=True).lower():
                        author = a_tag.get_text(strip=True)
        except Exception:
            pass

        try:
            el = soup.select_one("li.special")
            if el:
                price = self.normalize_price(el.get_text())
        except Exception:
            pass

        if price is None:
            try:
                meta = soup.select_one('meta[property="twitter:data1"]')
                if meta and meta.get("content"):
                    price = self.normalize_price(meta["content"])
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
        soup = self._get(self.SEARCH_URL, params={"search": query})
        if soup is None:
            return results

        links: list[str] = []
        for thumb in soup.select("div.product-thumb"):
            a_tag = thumb.select_one("h4 a") or thumb.select_one("div.caption a")
            if a_tag and a_tag.get("href"):
                href = a_tag["href"].split("?")[0]
                if href not in links:
                    links.append(href)

        for link in links:
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
