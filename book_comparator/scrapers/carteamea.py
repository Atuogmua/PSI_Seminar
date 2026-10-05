"""Scraper for carteamea.md bookstore (WooCommerce / Shoptimizer theme)."""

import re
import logging

from book_comparator.models.book import BookResult
from book_comparator.scrapers.base import BaseBookScraper

logger = logging.getLogger(__name__)

MAX_PAGES = 3


class CarteameaScraper(BaseBookScraper):
    """Scraper implementation for carteamea.md.

    WooCommerce site with Shoptimizer theme. Searches via /?s={query}&post_type=product.
    Handles pagination (first 3 pages via &paged=N).
    Products are in li.product with a.woocommerce-LoopProduct-link linking to /shop/slug/.
    Follows product links and extracts data from h1.product_title,
    p.price bdi (comma decimal separator), woocommerce-product-attributes table,
    product_meta, and short-description.
    """

    SHOP_NAME = "CarteaMea"
    BASE_URL = "https://carteamea.md"
    SEARCH_URL = "https://carteamea.md/"

    def _extract_product_links(self, soup) -> list[str]:
        links: list[str] = []
        for a_tag in soup.select("li.product a.woocommerce-LoopProduct-link"):
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
            bdi = soup.select_one("div.summary.entry-summary p.price span.woocommerce-Price-amount bdi")
            if not bdi:
                bdi = soup.select_one("p.price span.woocommerce-Price-amount bdi")
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
                    if "isbn" in label:
                        isbn = self.normalize_isbn(value)
                    elif "autor" in label or "author" in label:
                        author = value
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

        if not author:
            try:
                desc = soup.select_one("div.woocommerce-product-details__short-description")
                if desc:
                    text = desc.get_text()
                    m = re.search(r"Autor[:\s]*(.+)", text)
                    if m:
                        author = m.group(1).strip()
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
        seen_links: set[str] = set()

        for page in range(1, MAX_PAGES + 1):
            params: dict[str, str] = {"s": query, "post_type": "product"}
            if page > 1:
                params["paged"] = str(page)

            soup = self._get(self.SEARCH_URL, params=params)
            if soup is None:
                break

            links = self._extract_product_links(soup)
            new_links = [lnk for lnk in links if lnk not in seen_links]
            if not new_links:
                break

            for link in new_links:
                seen_links.add(link)
                result = self._parse_detail_page(link)
                if result:
                    results.append(result)

            next_link = soup.select_one("a.next.page-numbers")
            if not next_link:
                break

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
