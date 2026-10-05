"""Tests for each scraper with mocked HTTP responses."""

import responses

from book_comparator.scrapers.librarius import LibrariusScraper
from book_comparator.scrapers.carturesti import CarturestiScraper
from book_comparator.scrapers.biblion import BiblionScraper
from book_comparator.scrapers.carteamea import CarteameaScraper
from book_comparator.scrapers.bookzone import BookzoneScraper

# ---------------------------------------------------------------------------
# Minimal HTML snippets mimicking each shop's product card structure
# ---------------------------------------------------------------------------

LIBRARIUS_HTML_2_PRODUCTS = """
<html><body>
<div class="product-item">
  <h3><a href="/ro/book/1">Carte Unu</a></h3>
  <div class="author">Autor Unu</div>
  <div class="price">89,50 MDL</div>
</div>
<div class="product-item">
  <h3><a href="/ro/book/2">Carte Doi</a></h3>
  <div class="author">Autor Doi</div>
  <div class="price">120 MDL</div>
</div>
</body></html>
"""

LIBRARIUS_HTML_NO_RESULTS = "<html><body><p>Nu am gasit rezultate.</p></body></html>"

CARTURESTI_HTML_2_PRODUCTS = """
<html><body>
<div class="product">
  <h3><a href="/book/c1">Carte Alpha</a></h3>
  <div class="subtitle">Autor Alpha</div>
  <div class="special-price">75,00 MDL</div>
  <div class="price">100,00 MDL</div>
</div>
<div class="product">
  <h3><a href="/book/c2">Carte Beta</a></h3>
  <div class="subtitle">Autor Beta</div>
  <div class="price">55 MDL</div>
</div>
</body></html>
"""

CARTURESTI_HTML_NO_RESULTS = "<html><body><div class='no-results'></div></body></html>"

BIBLION_HTML_2_PRODUCTS = """
<html><body>
<div class="product-layout">
  <h4><a href="/product/b1">Carte Biblion 1</a></h4>
  <div class="author">Scriitor Unu</div>
  <div class="price">99,90 MDL</div>
</div>
<div class="product-layout">
  <h4><a href="/product/b2">Carte Biblion 2</a></h4>
  <div class="author">Scriitor Doi</div>
  <div class="price">45 MDL</div>
</div>
</body></html>
"""

BIBLION_HTML_NO_RESULTS = "<html><body><p>Niciun produs gasit.</p></body></html>"

CARTEAMEA_HTML_2_PRODUCTS = """
<html><body>
<div class="product-thumb">
  <h4><a href="/p/cm1">Carte CM 1</a></h4>
  <div class="author">Autor CM1</div>
  <div class="price">110 MDL</div>
</div>
<div class="product-thumb">
  <h4><a href="/p/cm2">Carte CM 2</a></h4>
  <div class="author">Autor CM2</div>
  <div class="price">65,50 MDL</div>
</div>
</body></html>
"""

CARTEAMEA_HTML_NO_RESULTS = "<html><body></body></html>"

BOOKZONE_HTML_2_PRODUCTS = """
<html><body>
<div class="product-card">
  <h3><a href="/bz/1">Carte BZ 1</a></h3>
  <div class="author">Autor BZ1</div>
  <div class="price">79 MDL</div>
</div>
<div class="product-card">
  <h3><a href="/bz/2">Carte BZ 2</a></h3>
  <div class="author">Autor BZ2</div>
  <div class="price">130,00 MDL</div>
</div>
</body></html>
"""

BOOKZONE_HTML_NO_RESULTS = "<html><body><div>0 results</div></body></html>"


# ---------------------------------------------------------------------------
# Librarius
# ---------------------------------------------------------------------------

class TestLibrariusScraper:
    @responses.activate
    def test_librarius_search_success(self):
        responses.add(
            responses.GET,
            "https://librarius.md/ro/search",
            body=LIBRARIUS_HTML_2_PRODUCTS,
            status=200,
        )
        scraper = LibrariusScraper()
        results = scraper.search_by_title("test")
        assert len(results) == 2
        assert all(r.shop_name == "Librarius" for r in results)
        assert all(r.title for r in results)
        assert results[0].title == "Carte Unu"
        assert results[0].price == 89.5

    @responses.activate
    def test_librarius_search_no_results(self):
        responses.add(
            responses.GET,
            "https://librarius.md/ro/search",
            body=LIBRARIUS_HTML_NO_RESULTS,
            status=200,
        )
        scraper = LibrariusScraper()
        results = scraper.search_by_title("nonexistent")
        assert results == []

    @responses.activate
    def test_librarius_search_http_error(self):
        responses.add(
            responses.GET,
            "https://librarius.md/ro/search",
            status=500,
        )
        scraper = LibrariusScraper()
        results = scraper.search_by_title("test")
        assert results == []


# ---------------------------------------------------------------------------
# Carturesti
# ---------------------------------------------------------------------------

class TestCarturestiScraper:
    @responses.activate
    def test_carturesti_search_success(self):
        responses.add(
            responses.GET,
            "https://carturesti.md/search/test",
            body=CARTURESTI_HTML_2_PRODUCTS,
            status=200,
        )
        scraper = CarturestiScraper()
        results = scraper.search_by_title("test")
        assert len(results) == 2
        assert all(r.shop_name == "Carturesti" for r in results)
        assert results[0].title == "Carte Alpha"
        assert results[0].price == 75.0  # discounted price preferred

    @responses.activate
    def test_carturesti_search_no_results(self):
        responses.add(
            responses.GET,
            "https://carturesti.md/search/nonexistent",
            body=CARTURESTI_HTML_NO_RESULTS,
            status=200,
        )
        scraper = CarturestiScraper()
        results = scraper.search_by_title("nonexistent")
        assert results == []

    @responses.activate
    def test_carturesti_search_http_error(self):
        responses.add(
            responses.GET,
            "https://carturesti.md/search/test",
            status=500,
        )
        scraper = CarturestiScraper()
        results = scraper.search_by_title("test")
        assert results == []


# ---------------------------------------------------------------------------
# Biblion
# ---------------------------------------------------------------------------

class TestBiblionScraper:
    @responses.activate
    def test_biblion_search_success(self):
        responses.add(
            responses.GET,
            "https://biblion.md/index.php",
            body=BIBLION_HTML_2_PRODUCTS,
            status=200,
        )
        scraper = BiblionScraper()
        results = scraper.search_by_title("test")
        assert len(results) == 2
        assert all(r.shop_name == "Biblion" for r in results)
        assert results[0].title == "Carte Biblion 1"

    @responses.activate
    def test_biblion_search_no_results(self):
        responses.add(
            responses.GET,
            "https://biblion.md/index.php",
            body=BIBLION_HTML_NO_RESULTS,
            status=200,
        )
        scraper = BiblionScraper()
        results = scraper.search_by_title("nonexistent")
        assert results == []

    @responses.activate
    def test_biblion_search_http_error(self):
        responses.add(
            responses.GET,
            "https://biblion.md/index.php",
            status=500,
        )
        scraper = BiblionScraper()
        results = scraper.search_by_title("test")
        assert results == []


# ---------------------------------------------------------------------------
# CarteaMea
# ---------------------------------------------------------------------------

class TestCarteameaScraper:
    @responses.activate
    def test_carteamea_search_success(self):
        responses.add(
            responses.GET,
            "https://carteamea.md/search",
            body=CARTEAMEA_HTML_2_PRODUCTS,
            status=200,
        )
        scraper = CarteameaScraper()
        results = scraper.search_by_title("test")
        assert len(results) == 2
        assert all(r.shop_name == "CarteaMea" for r in results)
        assert results[0].title == "Carte CM 1"

    @responses.activate
    def test_carteamea_search_no_results(self):
        responses.add(
            responses.GET,
            "https://carteamea.md/search",
            body=CARTEAMEA_HTML_NO_RESULTS,
            status=200,
        )
        scraper = CarteameaScraper()
        results = scraper.search_by_title("nonexistent")
        assert results == []

    @responses.activate
    def test_carteamea_search_http_error(self):
        responses.add(
            responses.GET,
            "https://carteamea.md/search",
            status=500,
        )
        scraper = CarteameaScraper()
        results = scraper.search_by_title("test")
        assert results == []


# ---------------------------------------------------------------------------
# Bookzone
# ---------------------------------------------------------------------------

class TestBookzoneScraper:
    @responses.activate
    def test_bookzone_search_success(self):
        responses.add(
            responses.GET,
            "https://bookzone.md/search",
            body=BOOKZONE_HTML_2_PRODUCTS,
            status=200,
        )
        scraper = BookzoneScraper()
        results = scraper.search_by_title("test")
        assert len(results) == 2
        assert all(r.shop_name == "Bookzone" for r in results)
        assert results[0].title == "Carte BZ 1"
        assert results[0].price == 79.0

    @responses.activate
    def test_bookzone_search_no_results(self):
        responses.add(
            responses.GET,
            "https://bookzone.md/search",
            body=BOOKZONE_HTML_NO_RESULTS,
            status=200,
        )
        scraper = BookzoneScraper()
        results = scraper.search_by_title("nonexistent")
        assert results == []

    @responses.activate
    def test_bookzone_search_http_error(self):
        responses.add(
            responses.GET,
            "https://bookzone.md/search",
            status=500,
        )
        scraper = BookzoneScraper()
        results = scraper.search_by_title("test")
        assert results == []
