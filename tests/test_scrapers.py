"""Tests for each scraper with mocked HTTP responses."""

import json

import responses

from book_comparator.scrapers.librarius import LibrariusScraper
from book_comparator.scrapers.carturesti import CarturestiScraper
from book_comparator.scrapers.biblion import BiblionScraper
from book_comparator.scrapers.carteamea import CarteameaScraper
from book_comparator.scrapers.bookzone import BookzoneScraper

# ---------------------------------------------------------------------------
# Librarius — JSON API at /ajax/search-drawer-suggest, detail at /ro/bookitem/
# ---------------------------------------------------------------------------

LIBRARIUS_SUGGEST_JSON = json.dumps({
    "success": True,
    "suggestions": [
        {
            "id": "100",
            "type": "book",
            "title": "Carte Unu",
            "subtitle": "Autor Unu",
            "price": "89",
            "image": "/img/placeholder.jpg",
            "url": "https://librarius.md/ro/bookitem/100",
        },
        {
            "id": "200",
            "type": "book",
            "title": "Carte Doi",
            "subtitle": "Autor Doi",
            "price": "120",
            "image": "/img/placeholder.jpg",
            "url": "https://librarius.md/ro/bookitem/200",
        },
    ],
    "currency": "lei",
})

LIBRARIUS_DETAIL_HTML = """
<html><body>
<div class="product-title-page">Carte Unu</div>
<div class="product-page-props-box">
  <div class="row book-props-item">
    <div class="book-prop-name">Autor</div>
    <div class="book-prop-value">Autor Unu</div>
  </div>
  <div class="row book-props-item">
    <div class="book-prop-name">ISBN</div>
    <div class="book-prop-value">978-9975-123-45-6</div>
  </div>
</div>
<button id="addToCartButton" data-price="89"></button>
</body></html>
"""

LIBRARIUS_DETAIL_HTML_2 = """
<html><body>
<div class="product-title-page">Carte Doi</div>
<div class="product-page-props-box">
  <div class="row book-props-item">
    <div class="book-prop-name">Autor</div>
    <div class="book-prop-value">Autor Doi</div>
  </div>
</div>
<button id="addToCartButton" data-price="120"></button>
</body></html>
"""


class TestLibrariusScraper:
    @responses.activate
    def test_librarius_search_success(self):
        responses.add(responses.GET, "https://librarius.md/ajax/search-drawer-suggest",
                      body=LIBRARIUS_SUGGEST_JSON, status=200, content_type="application/json")
        responses.add(responses.GET, "https://librarius.md/ro/bookitem/100",
                      body=LIBRARIUS_DETAIL_HTML, status=200)
        responses.add(responses.GET, "https://librarius.md/ro/bookitem/200",
                      body=LIBRARIUS_DETAIL_HTML_2, status=200)

        scraper = LibrariusScraper()
        results = scraper.search_by_title_or_author("test")
        assert len(results) == 2
        assert all(r.shop_name == "Librarius" for r in results)
        assert results[0].title == "Carte Unu"
        assert results[0].author == "Autor Unu"
        assert results[0].price == 89.0
        assert results[0].isbn == "9789975123456"

    @responses.activate
    def test_librarius_search_no_results(self):
        responses.add(responses.GET, "https://librarius.md/ajax/search-drawer-suggest",
                      json={"success": True, "suggestions": [], "currency": "lei"}, status=200)
        scraper = LibrariusScraper()
        results = scraper.search_by_title_or_author("nonexistent")
        assert results == []

    @responses.activate
    def test_librarius_search_http_error(self):
        responses.add(responses.GET, "https://librarius.md/ajax/search-drawer-suggest", status=500)
        scraper = LibrariusScraper()
        results = scraper.search_by_title_or_author("test")
        assert results == []


# ---------------------------------------------------------------------------
# Carturesti — CSRF + POST API at /product/simple-search, detail at /carte/
# ---------------------------------------------------------------------------

CARTURESTI_HOMEPAGE_HTML = """
<html><head>
<meta name="csrf-token" content="test-csrf-token-123"/>
</head><body></body></html>
"""

CARTURESTI_SEARCH_JSON = json.dumps({
    "0": {
        "id": "17207865",
        "img_url": "http://carturesti.md/img-prod/17207865.jpeg",
        "name": "Carte Alpha - Autor Alpha",
        "stock_label": ["in-local-stock"],
        "url": "/carte/carte-alpha-17207865?p=1&t=c_quick-search&s=test",
        "type": "carte",
    },
    "1": {
        "id": "97961903",
        "img_url": "http://carturesti.md/img-prod/97961903.jpeg",
        "name": "Carte Beta - Autor Beta",
        "stock_label": ["stoc-limitat"],
        "url": "/carte/carte-beta-97961903?p=2&t=c_quick-search&s=test",
        "type": "carte",
    },
    "attributeLinks": [],
    "categoryLinks": [],
    "staticPageLinks": [],
})

CARTURESTI_DETAIL_HTML = """
<html><body>
<div class="titlesContainer">
  <h1 class="titluProdus">Carte Alpha</h1>
  <div class="autorProdus">Autor Alpha</div>
</div>
<span class="pret">75<span class="bani">.00</span></span>
<div class="row detailsContainer">
  <div class="productAttr">
    <span class="productAttrLabel">ISBN:</span>
    <div>9786303057552</div>
  </div>
  <div class="productAttr">
    <span class="productAttrLabel">Editura:</span>
    <div>Editura Test</div>
  </div>
</div>
</body></html>
"""

CARTURESTI_DETAIL_HTML_2 = """
<html><body>
<h1 class="titluProdus">Carte Beta</h1>
<div class="autorProdus">Autor Beta</div>
<span class="pret">55<span class="bani">.00</span></span>
<div class="row detailsContainer"></div>
</body></html>
"""


class TestCarturestiScraper:
    @responses.activate
    def test_carturesti_search_success(self):
        responses.add(responses.GET, "https://carturesti.md",
                      body=CARTURESTI_HOMEPAGE_HTML, status=200)
        responses.add(responses.POST, "https://carturesti.md/product/simple-search",
                      body=CARTURESTI_SEARCH_JSON, status=200, content_type="application/json")
        responses.add(responses.GET, "https://carturesti.md/carte/carte-alpha-17207865",
                      body=CARTURESTI_DETAIL_HTML, status=200)
        responses.add(responses.GET, "https://carturesti.md/carte/carte-beta-97961903",
                      body=CARTURESTI_DETAIL_HTML_2, status=200)

        scraper = CarturestiScraper()
        results = scraper.search_by_title_or_author("test")
        assert len(results) == 2
        assert all(r.shop_name == "Carturesti" for r in results)
        assert results[0].title == "Carte Alpha"
        assert results[0].author == "Autor Alpha"
        assert results[0].price == 75.0
        assert results[0].isbn == "9786303057552"

    @responses.activate
    def test_carturesti_search_no_results(self):
        responses.add(responses.GET, "https://carturesti.md",
                      body=CARTURESTI_HOMEPAGE_HTML, status=200)
        responses.add(responses.POST, "https://carturesti.md/product/simple-search",
                      json={"attributeLinks": [], "categoryLinks": [], "staticPageLinks": []},
                      status=200)
        scraper = CarturestiScraper()
        results = scraper.search_by_title_or_author("nonexistent")
        assert results == []

    @responses.activate
    def test_carturesti_search_http_error(self):
        responses.add(responses.GET, "https://carturesti.md",
                      body=CARTURESTI_HOMEPAGE_HTML, status=200)
        responses.add(responses.POST, "https://carturesti.md/product/simple-search", status=500)
        scraper = CarturestiScraper()
        results = scraper.search_by_title_or_author("test")
        assert results == []


# ---------------------------------------------------------------------------
# Biblion — WooCommerce HTML search + detail pages
# ---------------------------------------------------------------------------

BIBLION_SEARCH_HTML = """
<html><body>
<ul class="products">
  <li class="product">
    <a class="woocommerce-LoopProduct-link" href="https://biblion.md/product/book-one/">
      <img src="placeholder.png"/>
    </a>
    <h3 class="woocommerce-loop-product__title">
      <a class="woocommerce-LoopProduct-link" href="https://biblion.md/product/book-one/">Carte Biblion 1</a>
    </h3>
    <span class="price"><span class="woocommerce-Price-amount amount"><bdi>275.00 <span class="woocommerce-Price-currencySymbol">MDL</span></bdi></span></span>
  </li>
</ul>
</body></html>
"""

BIBLION_DETAIL_HTML = """
<html><body>
<h1 class="product_title entry-title">Carte Biblion 1</h1>
<p class="price"><span class="woocommerce-Price-amount amount"><bdi>275.00 <span class="woocommerce-Price-currencySymbol">MDL</span></bdi></span></p>
<table class="woocommerce-product-attributes">
  <tr><th>Barcode</th><td class="woocommerce-product-attributes-item__value">9786060560722</td></tr>
</table>
<div class="product_meta">Артикул:48469</div>
</body></html>
"""


class TestBiblionScraper:
    @responses.activate
    def test_biblion_search_success(self):
        responses.add(responses.GET, "https://biblion.md/",
                      body=BIBLION_SEARCH_HTML, status=200)
        responses.add(responses.GET, "https://biblion.md/product/book-one/",
                      body=BIBLION_DETAIL_HTML, status=200)
        scraper = BiblionScraper()
        results = scraper.search_by_title_or_author("test")
        assert len(results) == 1
        assert results[0].shop_name == "Biblion"
        assert results[0].title == "Carte Biblion 1"
        assert results[0].price == 275.0
        assert results[0].isbn == "9786060560722"

    @responses.activate
    def test_biblion_search_no_results(self):
        responses.add(responses.GET, "https://biblion.md/",
                      body="<html><body><p>Niciun produs gasit.</p></body></html>", status=200)
        scraper = BiblionScraper()
        results = scraper.search_by_title_or_author("nonexistent")
        assert results == []

    @responses.activate
    def test_biblion_search_http_error(self):
        responses.add(responses.GET, "https://biblion.md/", status=500)
        scraper = BiblionScraper()
        results = scraper.search_by_title_or_author("test")
        assert results == []


# ---------------------------------------------------------------------------
# CarteaMea — WooCommerce HTML search (paginated) + detail pages
# ---------------------------------------------------------------------------

CARTEAMEA_SEARCH_HTML = """
<html><body>
<ul class="products">
  <li class="product">
    <a class="woocommerce-LoopProduct-link" href="https://carteamea.md/shop/book-one/">
      <img src="placeholder.png"/>
    </a>
    <div class="woocommerce-loop-product__title">
      <a class="woocommerce-LoopProduct-link" href="https://carteamea.md/shop/book-one/">
        <b>Autor CM1</b> Carte CM 1
      </a>
    </div>
    <span class="price"><span class="woocommerce-Price-amount amount"><bdi>150,00 <span class="woocommerce-Price-currencySymbol">MDL</span></bdi></span></span>
  </li>
</ul>
</body></html>
"""

CARTEAMEA_DETAIL_HTML = """
<html><body>
<div class="summary entry-summary">
  <h1 class="product_title entry-title">Carte CM 1</h1>
  <p class="price"><span class="woocommerce-Price-amount amount"><bdi>150,00 <span class="woocommerce-Price-currencySymbol">MDL</span></bdi></span></p>
  <div class="woocommerce-product-details__short-description">Descriere carte</div>
</div>
<div class="product_meta">SKU:CP130555</div>
</body></html>
"""


class TestCarteameaScraper:
    @responses.activate
    def test_carteamea_search_success(self):
        responses.add(responses.GET, "https://carteamea.md/",
                      body=CARTEAMEA_SEARCH_HTML, status=200)
        responses.add(responses.GET, "https://carteamea.md/shop/book-one/",
                      body=CARTEAMEA_DETAIL_HTML, status=200)
        scraper = CarteameaScraper()
        results = scraper.search_by_title_or_author("test")
        assert len(results) == 1
        assert results[0].shop_name == "CarteaMea"
        assert results[0].title == "Carte CM 1"
        assert results[0].price == 150.0

    @responses.activate
    def test_carteamea_search_no_results(self):
        responses.add(responses.GET, "https://carteamea.md/",
                      body="<html><body></body></html>", status=200)
        scraper = CarteameaScraper()
        results = scraper.search_by_title_or_author("nonexistent")
        assert results == []

    @responses.activate
    def test_carteamea_search_http_error(self):
        responses.add(responses.GET, "https://carteamea.md/", status=500)
        scraper = CarteameaScraper()
        results = scraper.search_by_title_or_author("test")
        assert results == []


# ---------------------------------------------------------------------------
# Bookzone — JSON API at api.bookzone.md/search + SSR detail at /carte/
# ---------------------------------------------------------------------------

BOOKZONE_SEARCH_JSON = json.dumps({
    "titles": [
        {
            "productId": 68730,
            "url": "carte-bz-one",
            "title": "Carte BZ 1",
            "subtitle": "",
            "oldPrice": 175.0,
            "price": 160.0,
            "mainImageUrl": "/upload/produse/img.jpg",
            "stock": 5,
            "isLinkable": True,
        },
    ],
    "authors": [],
    "suggestions": [],
    "categories": [],
})

BOOKZONE_DETAIL_HTML = """
<html><body>
<div class="prod">
  <div class="details__title">
    <a class="details__title__book" href="/autor/autor-bz1">Autor BZ1</a>
    <h1 class="details__title__name">Carte BZ 1</h1>
    <span class="details__title__volumes"></span>
  </div>
  <div class="details__info">
    <div class="details__info__price">
      <div class="details__info__price__old">
        <span class="details__info__price__old--cut">175 MDL</span>
        <span class="details__info__price__old--percent">-8.6%</span>
      </div>
      <span class="details__info__price__new">160 MDL</span>
    </div>
  </div>
  <div class="product_details">
    <div class="product_details_detail">
      <div class="product_details_detail_top">ISBN</div>
      <div class="product_details_detail_bottom">9786069748800</div>
    </div>
    <div class="product_details_detail">
      <div class="product_details_detail_top">Autor</div>
      <div class="product_details_detail_bottom">Autor BZ1</div>
    </div>
  </div>
</div>
</body></html>
"""


class TestBookzoneScraper:
    @responses.activate
    def test_bookzone_search_success(self):
        responses.add(responses.GET, "https://api.bookzone.md/search",
                      body=BOOKZONE_SEARCH_JSON, status=200, content_type="application/json")
        responses.add(responses.GET, "https://bookzone.md/carte/carte-bz-one",
                      body=BOOKZONE_DETAIL_HTML, status=200)
        scraper = BookzoneScraper()
        results = scraper.search_by_title_or_author("test")
        assert len(results) == 1
        assert results[0].shop_name == "Bookzone"
        assert results[0].title == "Carte BZ 1"
        assert results[0].author == "Autor BZ1"
        assert results[0].price == 160.0
        assert results[0].isbn == "9786069748800"

    @responses.activate
    def test_bookzone_search_no_results(self):
        responses.add(responses.GET, "https://api.bookzone.md/search",
                      json={"titles": [], "authors": [], "suggestions": [], "categories": []},
                      status=200)
        scraper = BookzoneScraper()
        results = scraper.search_by_title_or_author("nonexistent")
        assert results == []

    @responses.activate
    def test_bookzone_search_http_error(self):
        responses.add(responses.GET, "https://api.bookzone.md/search", status=500)
        scraper = BookzoneScraper()
        results = scraper.search_by_title_or_author("test")
        assert results == []
