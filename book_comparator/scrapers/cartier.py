"""Scraper for cartier.md bookstore (WooCommerce)."""

import re
import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class CartierScraper(BaseBookScraper):
    """Scraper implementation for cartier.md.

    WordPress/WooCommerce site. Searches via /?s={query}&post_type=product.
    Product cards in li.product with h2.woocommerce-loop-product__title.
    Detail pages have h1.product_title, span.woocommerce-Price-amount for price,
    and inline text for ISBN / author / publisher.
    """

    SHOP_NAME = "Cartier"
    BASE_URL = "https://cartier.md"
    SEARCH_URL = "https://cartier.md/"

    def _extract_product_links(self, soup) -> list[str]:
        links: list[str] = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/libraria/" in href and href.count("/") > 4 and href not in links:
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
            el = soup.select_one("h1.product_title")
            if el:
                title = el.get_text(strip=True)
        except Exception:
            pass

        try:
            for el in soup.select("span.woocommerce-Price-amount.amount"):
                p = self.normalize_price(el.get_text())
                if p is not None and p > 0:
                    price = p
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
            for a_tag in soup.select("a[href*='/carte-autor/']"):
                author = a_tag.get_text(strip=True)
                break
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
        soup = self._get(self.SEARCH_URL, params={"s": query, "post_type": "product"})
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
