"""Scraper for biblion.md bookstore (WooCommerce / Savoy theme)."""

import re
import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)


class BiblionScraper(BaseBookScraper):
    """Scraper implementation for biblion.md.

    WooCommerce site with Savoy theme. Searches via /?s={query}&post_type=product.
    Products are listed in li.product containers with a.woocommerce-LoopProduct-link.
    Follows product links to detail pages and extracts data from
    h1.product_title, p.price bdi, table.woocommerce-product-attributes,
    and div.product_meta.
    """

    SHOP_NAME = "Biblion"
    BASE_URL = "https://biblion.md"
    SEARCH_URL = "https://biblion.md/"

    def _extract_product_links(self, soup) -> list[str]:
        links: list[str] = []
        for a_tag in soup.select("li.product a.woocommerce-LoopProduct-link"):
            href = a_tag.get("href", "")
            if href and href not in links:
                links.append(href)
        if not links:
            for a_tag in soup.select("li.product a[href*='/product/']"):
                href = a_tag.get("href", "")
                if href and href not in links:
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
            el = soup.select_one("h1.product_title.entry-title")
            if el:
                title = el.get_text(strip=True)
        except Exception:
            pass

        try:
            bdi = soup.select_one("p.price span.woocommerce-Price-amount.amount bdi")
            if bdi:
                price = self.normalize_price(bdi.get_text())
        except Exception:
            pass

        try:
            tbl = soup.select_one("table.woocommerce-product-attributes")
            if tbl:
                for row in tbl.select("tr"):
                    th = row.select_one("th")
                    td = row.select_one("td.woocommerce-product-attributes-item__value")
                    if not td:
                        td = row.select_one("td:last-child")
                    if not th or not td:
                        continue
                    label = th.get_text(strip=True).lower()
                    value = td.get_text(strip=True)
                    if "isbn" in label or "barcode" in label:
                        isbn = self.normalize_isbn(value)
                    elif "autor" in label or "author" in label or "автор" in label:
                        author = value
        except Exception:
            pass

        if not author:
            try:
                desc = soup.select_one("div#tab-description")
                if desc:
                    m = re.search(r"autor\s*[–—\-:]\s*(.+?)(?:,|\.|editura|\n|$)",
                                  desc.get_text(), re.IGNORECASE)
                    if m:
                        author = m.group(1).strip()
            except Exception:
                pass

        if not isbn or not author:
            try:
                meta = soup.select_one("div.product_meta")
                if meta:
                    text = meta.get_text()
                    if not isbn:
                        m = re.search(r"ISBN[:\s]*([\d\-]{10,17})", text)
                        if m:
                            isbn = self.normalize_isbn(m.group(1))
            except Exception:
                pass

        if not isbn:
            try:
                text = soup.get_text()
                m = re.search(r"ISBN[:\s]*([\d\-]{10,17})", text)
                if m:
                    isbn = self.normalize_isbn(m.group(1))
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
