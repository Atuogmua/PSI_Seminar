"""Search orchestrator — runs all scrapers concurrently."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from book_comparator.models.book import BookResult
from book_comparator.scrapers import ALL_SCRAPERS
from book_comparator.scrapers.base import BaseScraper


def _run_scraper_search(
    scraper: BaseScraper,
    method: str,
    query: str,
) -> list[BookResult]:
    """Execute a single scraper's search method, returning results or empty list on error."""
    try:
        func = getattr(scraper, method)
        return func(query)
    except Exception as e:
        print(f"[{scraper.SHOP_NAME}] Error during {method}: {e}")
        return []


def search_all(
    query: str,
    search_type: str = "title",
    max_workers: int = 5,
) -> list[BookResult]:
    """Run all scrapers concurrently and return aggregated results.

    Args:
        query: The search term (ISBN, title, or author name).
        search_type: One of 'isbn', 'title', or 'author'.
        max_workers: Maximum number of concurrent threads.

    Returns:
        Combined list of BookResult from all scrapers, sorted by price ascending.
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
                print(f"[{scraper.SHOP_NAME}] Unexpected error: {e}")

    all_results.sort(key=lambda r: r.price)
    return all_results
