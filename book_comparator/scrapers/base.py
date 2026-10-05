"""Abstract base scraper defining the common interface for all bookstore scrapers."""

import logging
import random
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from book_comparator.models.book import BookResult

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 1


class BaseBookScraper(ABC):
    """Abstract base class for bookstore scrapers.

    All concrete scrapers must implement the three search methods.
    Provides a shared HTTP session with common headers, request throttling,
    and retry logic with exponential backoff.
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

    def _get(self, url: str, params: dict | None = None) -> BeautifulSoup | None:
        """Send GET request with retry logic, return parsed soup or None.

        - 10-second request timeout.
        - Retries up to 3 times with exponential backoff (1s, 2s, 4s).
        - Random delay between 0.5 and 1.5 seconds between requests to the same domain.
        - Logs every request URL at DEBUG level.
        - Returns None if all retries are exhausted.
        """
        elapsed = time.time() - self._last_request_time
        delay = random.uniform(0.5, 1.5)
        if elapsed < delay:
            time.sleep(delay - elapsed)

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.debug("[%s] GET %s params=%s (attempt %d/%d)",
                             self.SHOP_NAME, url, params, attempt, MAX_RETRIES)
                response = self.session.get(url, params=params, timeout=10)
                self._last_request_time = time.time()
                response.raise_for_status()
                return BeautifulSoup(response.text, "lxml")
            except requests.exceptions.RequestException as e:
                logger.warning("[%s] Request failed (attempt %d/%d): %s",
                               self.SHOP_NAME, attempt, MAX_RETRIES, e)
                if attempt < MAX_RETRIES:
                    backoff = BACKOFF_BASE * (2 ** (attempt - 1))
                    time.sleep(backoff)

        logger.error("[%s] All %d retries exhausted for %s", self.SHOP_NAME, MAX_RETRIES, url)
        return None

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
    def search_by_title_or_author(self, query: str) -> list[BookResult]:
        """Search for books by title or author name."""
        ...
