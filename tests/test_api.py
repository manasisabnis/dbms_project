from fastapi.testclient import TestClient

from backend.app.deps import get_db
from backend.app.main import app


def client_for(db):
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_health():
    assert TestClient(app).get("/api/health").json() == {"status": "ok"}


def test_dashboard_shape_and_ordering(db_with_stats):
    r = client_for(db_with_stats).get("/api/trends/dashboard?window=3&limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["window_years"] == 3
    assert body["counts"]["emerging"] > 0
    growths = [c["growth_pct"] for c in body["emerging"]]
    assert growths == sorted(growths, reverse=True)           # biggest rise first
    drops = [c["growth_pct"] for c in body["declining"]]
    assert drops == sorted(drops)                             # biggest drop first
    cited = [c["total_citations"] for c in body["most_cited"]]
    assert cited == sorted(cited, reverse=True)
    assert all(c["label"] == "emerging" for c in body["emerging"])


def test_dashboard_rejects_bad_window(db_with_stats):
    assert client_for(db_with_stats).get("/api/trends/dashboard?window=7").status_code == 422


def test_case_trend(db_with_stats):
    c = client_for(db_with_stats)
    top = c.get("/api/trends/dashboard").json()["most_cited"][0]
    r = c.get(f"/api/cases/{top['case_id']}/citation-trend")
    assert r.status_code == 200
    body = r.json()
    assert sum(y["count"] for y in body["yearly"]) == body["total_citations"]
    assert sum(x["count"] for x in body["by_court_level"]) == body["total_citations"]
    assert set(body["windows"]) == {"1", "3", "5"}


def test_case_trend_404(db_with_stats):
    assert client_for(db_with_stats).get("/api/cases/999999/citation-trend").status_code == 404
