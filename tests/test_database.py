"""Tests for the SQLite database layer."""

from book_comparator.models.book import BookResult, SearchSession
from book_comparator.services.database import Database

FIXED_TS = "2026-10-05T12:00:00+00:00"


def _make_session(**overrides) -> SearchSession:
    defaults = dict(id=None, query="test", search_type="title", timestamp=FIXED_TS)
    defaults.update(overrides)
    return SearchSession(**defaults)


def _make_result(session_id: int, **overrides) -> BookResult:
    defaults = dict(
        id=None,
        isbn=None,
        title="Book",
        author=None,
        price=100.0,
        currency="MDL",
        source_url="https://example.com",
        shop_name="TestShop",
        session_id=session_id,
        scraped_at=FIXED_TS,
    )
    defaults.update(overrides)
    return BookResult(**defaults)


class TestSaveAndGetSession:
    def test_save_and_get_session(self, tmp_db):
        session = _make_session(query="Eminescu", search_type="author")
        sid = tmp_db.save_session(session)
        assert sid is not None

        fetched = tmp_db.get_session(sid)
        assert fetched is not None
        assert fetched.id == sid
        assert fetched.query == "Eminescu"
        assert fetched.search_type == "author"
        assert fetched.timestamp == FIXED_TS


class TestSaveAndRetrieveResults:
    def test_save_results_and_retrieve(self, tmp_db, sample_session, sample_results):
        sid = tmp_db.save_session(sample_session)
        for r in sample_results:
            r.session_id = sid
        tmp_db.save_results(sample_results)

        fetched = tmp_db.get_results(sid)
        assert len(fetched) == 3

    def test_get_results_sorted_by_price(self, tmp_db):
        sid = tmp_db.save_session(_make_session())
        results = [
            _make_result(sid, title="Expensive", price=120.0),
            _make_result(sid, title="Cheap", price=89.0),
            _make_result(sid, title="No Price", price=None),
        ]
        tmp_db.save_results(results)

        fetched = tmp_db.get_results(sid)
        assert fetched[0].price == 89.0
        assert fetched[1].price == 120.0
        assert fetched[2].price is None


class TestGetBestPrice:
    def test_get_best_price(self, tmp_db, sample_session, sample_results):
        sid = tmp_db.save_session(sample_session)
        for r in sample_results:
            r.session_id = sid
        tmp_db.save_results(sample_results)

        best = tmp_db.get_best_price(sid)
        assert best is not None
        assert best.price == 89.0
        assert best.title == "Poezii"

    def test_get_best_price_no_results(self, tmp_db):
        sid = tmp_db.save_session(_make_session())
        best = tmp_db.get_best_price(sid)
        assert best is None


class TestGetAllSessions:
    def test_get_all_sessions_order(self, tmp_db):
        s1 = tmp_db.save_session(_make_session(query="first"))
        s2 = tmp_db.save_session(_make_session(query="second"))
        s3 = tmp_db.save_session(_make_session(query="third"))

        sessions = tmp_db.get_all_sessions()
        assert len(sessions) == 3
        assert sessions[0].query == "third"
        assert sessions[1].query == "second"
        assert sessions[2].query == "first"


class TestTablesCreated:
    def test_tables_created_on_init(self, tmp_path):
        db = Database(str(tmp_path / "fresh.db"))
        rows = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [r[0] for r in rows]
        assert "book_results" in table_names
        assert "search_sessions" in table_names
        db.close()
