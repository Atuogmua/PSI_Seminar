"""Abstract base scraper defining the common interface for all bookstore scrapers."""

import logging
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from book_comparator.models.book import BookResult

logger = logging.getLogger(__name__)


class BaseBookScraper(ABC):
    """Abstract base class for bookstore scrapers.

    All concrete scrapers must implement the three search methods.
    Provides a shared HTTP session with common headers and request throttling.
    """

    SHOP_NAME: str = ""
    BASE_URL: str = ""
    SEARCH_URL: str = ""
    HEADERS: dict = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
    }

    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._last_request_time: float = 0.0

    def _get(self, url: str, params: dict | None = None) -> BeautifulSoup:
        """Send GET request with self.HEADERS, raise on HTTP errors, return parsed soup (lxml parser).

        Enforces a 1-second delay between consecutive requests to the same domain.
        Logs every request URL at DEBUG level.
        """
        elapsed = time.time() - self._last_request_time
        if elapsed < 1.0:
            time.sleep(1.0 - elapsed)

        logger.debug("[%s] GET %s params=%s", self.SHOP_NAME, url, params)
        response = self.session.get(url, params=params, timeout=15)
        self._last_request_time = time.time()
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    @staticmethod
    def normalize_isbn(raw: str | None) -> str | None:
        """Remove hyphens and validate ISBN length (10 or 13 digits).

        Returns the cleaned ISBN string or None if invalid.
        """
        if not raw:
            return None
        cleaned = re.sub(r"[^0-9X]", "", raw.strip().upper())
        if len(cleaned) in (10, 13):
            return cleaned
        return None

    @staticmethod
    def normalize_price(raw: str) -> float | None:
        """Strip currency words, whitespace, and commas; parse as float.

        Returns None if parsing fails.
        """
        text = raw.replace("lei", "").replace("LEI", "").replace("MDL", "")
        text = text.replace("mdl", "").replace("\xa0", "").replace(" ", "")
        text = text.replace(",", ".").strip()
        text = re.sub(r"[^\d.]", "", text)
        try:
            return float(text)
        except ValueError:
            return None

    @staticmethod
    def _now_iso() -> str:
        """Return the current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

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
