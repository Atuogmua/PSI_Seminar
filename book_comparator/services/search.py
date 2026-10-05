"""Search orchestrator — runs all scrapers concurrently and persists results."""

import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.scrapers import ALL_SCRAPERS
from book_comparator.scrapers.base import BaseBookScraper
from book_comparator.services.database import Database

logger = logging.getLogger(__name__)

SCRAPER_TIMEOUT = 30


def _run_scraper_search(
    scraper: BaseBookScraper,
    method: str,
    query: str,
) -> list[BookResult]:
    """Execute a single scraper's search method."""
    func = getattr(scraper, method)
    return func(query)


def search_all(
    query: str,
    search_type: str = "title",
    max_workers: int = 5,
) -> tuple[list[BookResult], SearchSession, int]:
    """Run all scrapers concurrently, persist results to SQLite, and return them.

    Args:
        query: The search term (ISBN, title, or author name).
        search_type: One of 'isbn', 'title', or 'author'.
        max_workers: Maximum number of concurrent threads.

    Returns:
        Tuple of (results sorted by price ascending with NULLs last,
                  SearchSession, number of failed scrapers).
    """
    method_map = {
        "isbn": "search_by_isbn",
        "title": "search_by_title",
        "author": "search_by_author",
    }
    method = method_map.get(search_type, "search_by_title")

    scrapers = [cls() for cls in ALL_SCRAPERS]
    all_results: list[BookResult] = []
    failed_count = 0
    completed_futures: set = set()

    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {
        executor.submit(_run_scraper_search, scraper, method, query): scraper
        for scraper in scrapers
    }

    try:
        for future in as_completed(futures, timeout=SCRAPER_TIMEOUT):
            completed_futures.add(future)
            scraper = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception:
                logger.error("[%s] Unexpected error — skipping:\n%s",
                             scraper.SHOP_NAME, traceback.format_exc())
                failed_count += 1
    except TimeoutError:
        for future, scraper in futures.items():
            if future not in completed_futures:
                logger.warning("[%s] Timed out after %ds — skipping",
                               scraper.SHOP_NAME, SCRAPER_TIMEOUT)
                failed_count += 1
                future.cancel()

    executor.shutdown(wait=False, cancel_futures=True)

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
    return all_results, session, failed_count
