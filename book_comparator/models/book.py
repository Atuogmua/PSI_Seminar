"""Data models for book search results."""

from dataclasses import dataclass


@dataclass
class BookResult:
    """Represents a single book result from a bookstore scraper."""

    isbn: str | None
    title: str
    author: str | None
    price: float
    currency: str
    source_url: str
    shop_name: str
