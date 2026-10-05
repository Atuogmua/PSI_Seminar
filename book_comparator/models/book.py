"""Data models for book search results and search sessions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class SearchSession:
    """Represents a single search session initiated by the user."""

    id: int | None
    query: str
    search_type: str
    timestamp: str

    @staticmethod
    def create(query: str, search_type: str) -> "SearchSession":
        """Create a new SearchSession with the current UTC timestamp."""
        return SearchSession(
            id=None,
            query=query,
            search_type=search_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


@dataclass
class BookResult:
    """Represents a single book result from a bookstore scraper."""

    id: int | None
    isbn: str | None
    title: str
    author: str | None
    price: float | None
    currency: str
    source_url: str
    shop_name: str
    session_id: int
    scraped_at: str

    def price_display(self) -> str:
        """Return formatted price string, e.g. '149.00 MDL', or 'N/A' if price is None."""
        if self.price is None:
            return "N/A"
        return f"{self.price:.2f} {self.currency}"
