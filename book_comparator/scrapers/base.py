"""Abstract base scraper defining the common interface for all bookstore scrapers."""

from abc import ABC, abstractmethod

import requests
from bs4 import BeautifulSoup

from book_comparator.models.book import BookResult


class BaseScraper(ABC):
    """Abstract base class for bookstore scrapers.

    All concrete scrapers must implement the three search methods.
    Provides a shared HTTP session with common headers.
    """

    BASE_URL: str = ""
    SHOP_NAME: str = ""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
        })

    def _get_soup(self, url: str, params: dict | None = None) -> BeautifulSoup:
        """Fetch a URL and return a BeautifulSoup object."""
        response = self.session.get(url, params=params, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    @abstractmethod
    def search_by_isbn(self, isbn: str) -> list[BookResult]:
        """Search for books by ISBN."""
        ...

    @abstractmethod
    def search_by_title(self, title: str) -> list[BookResult]:
        """Search for books by title."""
        ...

    @abstractmethod
    def search_by_author(self, author: str) -> list[BookResult]:
        """Search for books by author name."""
        ...
