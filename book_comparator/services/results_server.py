"""Generates an HTML comparison table and opens it in the default browser."""

import os
import re
import tempfile
import webbrowser
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.services.database import Database

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")

SHOP_NAMES = [
    "Librarius", "Carturesti", "Biblion", "Bookzone",
    # "CarteaMea",
    "Litera", "BookStore", "Cartier", "Cartego", "Dorinta",
    # "Elefant", "Mesageria",
]


def _group_key(book: BookResult) -> str:
    if book.isbn:
        return f"isbn:{book.isbn.strip()}"
    return f"title:{re.sub(r'\\s+', ' ', book.title.strip().lower())}"


def _group_results(results: list[BookResult]) -> list[dict]:
    groups: dict[str, dict] = {}
    order: list[str] = []

    for book in results:
        key = _group_key(book)
        if key not in groups:
            groups[key] = {
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "shops": {},
                "best_price": None,
            }
            order.append(key)

        g = groups[key]
        if book.author and not g["author"]:
            g["author"] = book.author
        if book.isbn and not g["isbn"]:
            g["isbn"] = book.isbn

        g["shops"][book.shop_name] = {
            "price": book.price,
            "currency": book.currency,
            "display": book.price_display(),
            "url": book.source_url,
        }

        if book.price is not None:
            if g["best_price"] is None or book.price < g["best_price"]:
                g["best_price"] = book.price

    grouped = [groups[k] for k in order]
    grouped.sort(key=lambda g: (g["best_price"] is None, g["best_price"] or 0))
    return grouped


def serve_results(session: SearchSession) -> None:
    """Render results for a search session to a temp HTML file and open it in the browser."""
    db = Database()
    try:
        results = db.get_results(session.id) if session.id else []
    finally:
        db.close()

    grouped = _group_results(results)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("results.html")
    html = template.render(
        query=session.query,
        search_type="Title / Author" if session.search_type == "title_author" else session.search_type.upper(),
        timestamp=session.timestamp,
        grouped=grouped,
        shop_names=SHOP_NAMES,
        result_count=len(results),
        book_count=len(grouped),
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".html",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(html)
        tmp_path = f.name

    webbrowser.open("file://" + tmp_path)
