"""SQLite database layer for persisting search sessions and book results."""

import sqlite3

from book_comparator.models.book import BookResult, SearchSession

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS search_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    search_type TEXT NOT NULL CHECK(search_type IN ('isbn','title','author','title_author')),
    timestamp TEXT NOT NULL
);
"""

_CREATE_RESULTS = """
CREATE TABLE IF NOT EXISTS book_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT,
    title TEXT NOT NULL,
    author TEXT,
    price REAL,
    currency TEXT NOT NULL DEFAULT 'MDL',
    source_url TEXT NOT NULL,
    shop_name TEXT NOT NULL,
    session_id INTEGER NOT NULL,
    scraped_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES search_sessions(id)
);
"""


class Database:
    """SQLite database for storing search sessions and book results."""

    def __init__(self, db_path: str = "bookcompare.db") -> None:
        """Open connection, enable WAL mode, create tables if missing."""
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self._migrate_schema()
        self.conn.commit()

    def _migrate_schema(self) -> None:
        """Create tables or migrate from older schemas."""
        existing = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='search_sessions'"
        ).fetchone()

        if existing:
            sql = self.conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='search_sessions'"
            ).fetchone()[0]
            if "'title_author'" not in sql:
                self.conn.execute("PRAGMA foreign_keys=OFF;")
                self.conn.execute("ALTER TABLE search_sessions RENAME TO _sessions_old")
                self.conn.execute(_CREATE_SESSIONS)
                self.conn.execute(
                    "INSERT INTO search_sessions (id, query, search_type, timestamp) "
                    "SELECT id, query, search_type, timestamp FROM _sessions_old"
                )
                self.conn.execute("DROP TABLE _sessions_old")
                self.conn.execute("PRAGMA foreign_keys=ON;")
        else:
            self.conn.execute(_CREATE_SESSIONS)

        self.conn.execute(_CREATE_RESULTS)

    def save_session(self, session: SearchSession) -> int:
        """Insert a session row, return its id."""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO search_sessions (query, search_type, timestamp) VALUES (?, ?, ?)",
                (session.query, session.search_type, session.timestamp),
            )
            session.id = cursor.lastrowid
            return session.id

    def save_results(self, results: list[BookResult]) -> None:
        """Bulk-insert results using executemany."""
        rows = [
            (r.isbn, r.title, r.author, r.price, r.currency,
             r.source_url, r.shop_name, r.session_id, r.scraped_at)
            for r in results
        ]
        with self.conn:
            self.conn.executemany(
                "INSERT INTO book_results "
                "(isbn, title, author, price, currency, source_url, shop_name, session_id, scraped_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )

    def get_session(self, session_id: int) -> SearchSession | None:
        """Fetch one session by id."""
        row = self.conn.execute(
            "SELECT id, query, search_type, timestamp FROM search_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return SearchSession(id=row[0], query=row[1], search_type=row[2], timestamp=row[3])

    def get_results(self, session_id: int) -> list[BookResult]:
        """Fetch all results for a session, sorted by price ascending (NULLs last)."""
        rows = self.conn.execute(
            "SELECT id, isbn, title, author, price, currency, source_url, shop_name, session_id, scraped_at "
            "FROM book_results WHERE session_id = ? "
            "ORDER BY CASE WHEN price IS NULL THEN 1 ELSE 0 END, price ASC",
            (session_id,),
        ).fetchall()
        return [
            BookResult(
                id=r[0], isbn=r[1], title=r[2], author=r[3], price=r[4],
                currency=r[5], source_url=r[6], shop_name=r[7],
                session_id=r[8], scraped_at=r[9],
            )
            for r in rows
        ]

    def get_all_sessions(self) -> list[SearchSession]:
        """Return all past sessions, newest first."""
        rows = self.conn.execute(
            "SELECT id, query, search_type, timestamp FROM search_sessions ORDER BY id DESC"
        ).fetchall()
        return [
            SearchSession(id=r[0], query=r[1], search_type=r[2], timestamp=r[3])
            for r in rows
        ]

    def get_best_price(self, session_id: int) -> BookResult | None:
        """Return the cheapest result for a session, or None."""
        row = self.conn.execute(
            "SELECT id, isbn, title, author, price, currency, source_url, shop_name, session_id, scraped_at "
            "FROM book_results WHERE session_id = ? AND price IS NOT NULL "
            "ORDER BY price ASC LIMIT 1",
            (session_id,),
        ).fetchone()
        if row is None:
            return None
        return BookResult(
            id=row[0], isbn=row[1], title=row[2], author=row[3], price=row[4],
            currency=row[5], source_url=row[6], shop_name=row[7],
            session_id=row[8], scraped_at=row[9],
        )

    def close(self) -> None:
        """Close the connection."""
        self.conn.close()
