"""Generates an HTML comparison table and opens it in the default browser."""

import os
import tempfile
import webbrowser

from jinja2 import Environment, FileSystemLoader

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.services.database import Database

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def serve_results(session: SearchSession) -> None:
    """Render results for a search session to a temp HTML file and open it in the browser.

    Fetches results from the database using the session id, renders the Jinja2
    template, writes to a temporary .html file, and opens it with webbrowser.

    Args:
        session: The SearchSession whose results should be displayed.
    """
    db = Database()
    try:
        results = db.get_results(session.id) if session.id else []
    finally:
        db.close()

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("results.html")
    html = template.render(
        query=session.query,
        search_type=session.search_type,
        timestamp=session.timestamp,
        results=results,
        result_count=len(results),
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
