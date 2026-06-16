import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from gitflow.dashboard.api.main import app
from gitflow.dashboard.api.schemas import FilterParams, SearchParams, ExportParams
from pydantic import ValidationError

client = TestClient(app)

class TestApiHardening:
    def test_health_endpoints(self, db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: db_session)

        # Liveness
        resp = client.get("/health/live")
        assert resp.status_code == 200
        assert resp.json() == {'status': 'alive'}

        # Readiness
        resp = client.get("/health/ready")
        assert resp.status_code == 200
        assert resp.json()['status'] == 'ready'

        # Full health check
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()['status'] == 'healthy'

    def test_readiness_probe_db_fail(self, monkeypatch):
        # Mock HealthChecker.check_db_connection to return passed=False
        from gitflow.dashboard.api.health import HealthChecker
        mock_check = {"passed": False, "detail": "Connection error", "name": "Database Connection"}
        monkeypatch.setattr(HealthChecker, "check_db_connection", lambda self: mock_check)
        
        # We also need a dummy session
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: MagicMock())

        from unittest.mock import MagicMock
        resp = client.get("/health/ready")
        assert resp.status_code == 503
        assert resp.json()['status'] == 'not ready'

    def test_health_check_fail(self, monkeypatch):
        from gitflow.dashboard.api.health import HealthChecker
        mock_check = {"healthy": False, "status": "unhealthy", "checks": []}
        monkeypatch.setattr(HealthChecker, "full_health_check", lambda self: mock_check)
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: MagicMock())

        from unittest.mock import MagicMock
        resp = client.get("/health")
        assert resp.status_code == 503
        assert resp.json()['status'] == 'unhealthy'

    def test_input_validation_filter_valid(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/filter?days=30&per_page=10")
        assert resp.status_code == 200
        data = resp.json()
        assert 'total' in data
        assert 'results' in data

    def test_input_validation_filter_invalid_days(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/filter?days=999")
        assert resp.status_code == 422
        assert 'detail' in resp.json()

    def test_input_validation_search_valid(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/search?q=feat&category=commits")
        assert resp.status_code == 200
        data = resp.json()
        assert 'results' in data

    def test_input_validation_search_invalid_category(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/search?q=feat&category=invalid_cat")
        assert resp.status_code == 422

    def test_api_export_json(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.post("/api/export?format=json&days=10")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_api_export_csv(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.post("/api/export?format=csv&days=10")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    def test_api_export_markdown(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.post("/api/export?format=markdown&days=10")
        assert resp.status_code == 200
        assert "text/markdown" in resp.headers["content-type"]

    def test_rate_limiting_exceeded(self):
        status_codes = []
        for _ in range(11):
            resp = client.get("/api/dashboard")
            status_codes.append(resp.status_code)

        assert 429 in status_codes
        resp_429 = client.get("/api/dashboard")
        assert resp_429.status_code == 429
        assert resp_429.json() == {"error": "Rate limit exceeded. Try again later."}

        from gitflow.dashboard.api.limiter import limiter
        limiter._storage.reset()

    def test_get_dashboard(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert 'today' in data
        assert 'productivity_score' in data

    def test_get_history(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/history/30")
        assert resp.status_code == 200
        assert 'data' in resp.json()

    def test_get_repos(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/repos")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_streaks(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/streaks")
        assert resp.status_code == 200
        assert 'streaks' in resp.json()

    def test_search_files_and_authors(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        
        # Test files category search
        resp = client.get("/api/search?q=main&category=files")
        assert resp.status_code == 200
        assert resp.json()['results'][0]['type'] == 'file'

        # Test authors category search
        resp = client.get("/api/search?q=Test&category=authors")
        assert resp.status_code == 200
        assert resp.json()['results'][0]['type'] == 'author'

    def test_get_authors(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/authors")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_hot_files(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/hot-files?days=30")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_commits_by_language(self, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        resp = client.get("/api/commit-by-language?days=30")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @patch('asyncio.sleep', side_effect=InterruptedError)
    def test_websocket_live(self, mock_sleep, seeded_db_session, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.main.get_session", lambda: seeded_db_session)
        
        # The while True loop calls asyncio.sleep(30). Raising InterruptedError terminates it.
        try:
            with client.websocket_connect("/ws/live") as websocket:
                data = websocket.receive_json()
                assert 'timestamp' in data
                assert 'commits_today' in data
                assert 'score' in data
        except InterruptedError:
            pass
