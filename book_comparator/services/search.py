"""Search orchestrator — runs all scrapers concurrently and persists results."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.scrapers import ALL_SCRAPERS
from book_comparator.scrapers.base import BaseBookScraper
from book_comparator.services.database import Database

logger = logging.getLogger(__name__)


def _run_scraper_search(
    scraper: BaseBookScraper,
    method: str,
    query: str,
) -> list[BookResult]:
    """Execute a single scraper's search method, returning results or empty list on error."""
    try:
        func = getattr(scraper, method)
        return func(query)
    except Exception as e:
        logger.error("[%s] Error during %s: %s", scraper.SHOP_NAME, method, e)
        return []


def search_all(
    query: str,
    search_type: str = "title",
    max_workers: int = 5,
) -> tuple[list[BookResult], SearchSession]:
    """Run all scrapers concurrently, persist results to SQLite, and return them.

    Args:
        query: The search term (ISBN, title, or author name).
        search_type: One of 'isbn', 'title', or 'author'.
        max_workers: Maximum number of concurrent threads.

    Returns:
        Tuple of (results sorted by price ascending with NULLs last, SearchSession).
    """
    method_map = {
        "isbn": "search_by_isbn",
        "title": "search_by_title",
        "author": "search_by_author",
    }
    method = method_map.get(search_type, "search_by_title")

    scrapers = [cls() for cls in ALL_SCRAPERS]
    all_results: list[BookResult] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_run_scraper_search, scraper, method, query): scraper
            for scraper in scrapers
        }

        for future in as_completed(futures):
            scraper = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.error("[%s] Unexpected error: %s", scraper.SHOP_NAME, e)

    db = Database()
    try:
        session = SearchSession.create(query, search_type)
        session_id = db.save_session(session)

        for r in all_results:
            r.session_id = session_id

        if all_results:
            db.save_results(all_results)
    finally:
        db.close()

    all_results.sort(key=lambda r: (r.price is None, r.price or 0))
    return all_results, session
