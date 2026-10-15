from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.mysql_db import get_mysql_connection


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.query = ""
        self.params = ()

    def execute(self, query, params=()):
        self.query = query
        self.params = params

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False
        self.last_cursor = None

    def cursor(self, dictionary=False):
        self.last_cursor = FakeCursor(self.rows)
        return self.last_cursor

    def close(self):
        self.closed = True


def test_search_cases_returns_rows():
    fake = FakeConnection([
        {"case_id": 1, "case_name": "Example v. State",
         "case_number": "EX/1", "court_name": "Supreme Court"}
    ])
    app.dependency_overrides[get_mysql_connection] = lambda: fake
    try:
        response = TestClient(app).get("/api/cases?q=Example")
        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["cases"][0]["case_id"] == 1
        assert fake.closed
    finally:
        app.dependency_overrides.pop(get_mysql_connection, None)


def test_get_case_returns_404_when_missing():
    fake = FakeConnection([])
    app.dependency_overrides[get_mysql_connection] = lambda: fake
    try:
        response = TestClient(app).get("/api/cases/99999")
        assert response.status_code == 404
        assert fake.closed
    finally:
        app.dependency_overrides.pop(get_mysql_connection, None)


def test_search_limit_is_validated():
    # FastAPI should reject invalid limits before accessing MySQL.
    fake = FakeConnection([])
    app.dependency_overrides[get_mysql_connection] = lambda: fake
    try:
        response = TestClient(app).get("/api/cases?limit=1000")
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_mysql_connection, None)
