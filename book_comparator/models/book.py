"""Data models for book search results."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass
class BookResult:
    """Represents a single book result from a bookstore scraper."""

    isbn: str
    title: str
    author: str
    price: Decimal
    currency: str
    source_url: str
    shop_name: str
