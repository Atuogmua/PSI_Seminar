"""Shared fixtures for the test suite."""

import pytest

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.services.database import Database

FIXED_TIMESTAMP = "2026-10-05T12:00:00+00:00"


@pytest.fixture
def tmp_db(tmp_path):
    """Create a Database instance pointing to a temporary SQLite file."""
    db = Database(str(tmp_path / "test.db"))
    yield db
    db.close()


@pytest.fixture
def sample_session() -> SearchSession:
    """Return a SearchSession with fixed values."""
    return SearchSession(
        id=None,
        query="Eminescu",
        search_type="author",
        timestamp=FIXED_TIMESTAMP,
    )


@pytest.fixture
def sample_results() -> list[BookResult]:
    """Return 3 BookResult objects with known prices for predictable assertions."""
    return [
        BookResult(
            id=None,
            isbn="9789975741234",
            title="Poezii",
            author="Mihai Eminescu",
            price=89.0,
            currency="MDL",
            source_url="https://librarius.md/poezii",
            shop_name="Librarius",
            session_id=0,
            scraped_at=FIXED_TIMESTAMP,
        ),
        BookResult(
            id=None,
            isbn="9789975741235",
            title="Luceafarul",
            author="Mihai Eminescu",
            price=120.0,
            currency="MDL",
            source_url="https://carturesti.md/luceafarul",
            shop_name="Carturesti",
            session_id=0,
            scraped_at=FIXED_TIMESTAMP,
        ),
        BookResult(
            id=None,
            isbn=None,
            title="Opere Complete",
            author="Mihai Eminescu",
            price=None,
            currency="MDL",
            source_url="https://biblion.md/opere",
            shop_name="Biblion",
            session_id=0,
            scraped_at=FIXED_TIMESTAMP,
        ),
    ]
