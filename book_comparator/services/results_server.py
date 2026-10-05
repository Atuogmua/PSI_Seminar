"""Generates an HTML comparison table and serves it on localhost."""

import os
import threading
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from jinja2 import Environment, FileSystemLoader

from book_comparator.models.book import BookResult

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")


def render_results(results: list[BookResult], query: str, search_type: str) -> str:
    """Render search results into an HTML string using the Jinja2 template.

    Args:
        results: List of BookResult to display.
        query: The original search query.
        search_type: The type of search performed.

    Returns:
        Rendered HTML string.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)
    template = env.get_template("results.html")
    return template.render(results=results, query=query, search_type=search_type)


def serve_results(
    results: list[BookResult],
    query: str,
    search_type: str,
    port: int = 8080,
    open_browser: bool = True,
) -> HTTPServer:
    """Generate HTML and serve it on localhost.

    Args:
        results: List of BookResult to display.
        query: The original search query.
        search_type: The type of search performed.
        port: Port number for the HTTP server.
        open_browser: Whether to open the results in a browser automatically.

    Returns:
        The running HTTPServer instance.
    """
    html_content = render_results(results, query, search_type)

    class ResultHandler(SimpleHTTPRequestHandler):
        """Handler that serves the rendered HTML."""

        def do_GET(self) -> None:
            """Serve the results HTML page."""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html_content.encode("utf-8"))

        def log_message(self, format: str, *args) -> None:
            """Suppress default request logging."""
            pass

    server = HTTPServer(("127.0.0.1", port), ResultHandler)

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{port}")

    return server
