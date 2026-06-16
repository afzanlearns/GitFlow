import pytest
from datetime import datetime, timedelta
from click.testing import CliRunner
from gitflow.cli.main import cli
from gitflow.dashboard.api.health import HealthChecker
from gitflow.models import ServiceStatus, Repository

class TestHealthAndStatus:
    def test_check_db_connection(self, db_session):
        checker = HealthChecker(db_session)
        res = checker.check_db_connection()
        assert res['passed'] is True
        assert res['name'] == 'Database Connection'

    def test_check_last_scrape_empty(self, db_session):
        checker = HealthChecker(db_session)
        res = checker.check_last_scrape()
        assert res['passed'] is True
        assert 'No scrapes yet' in res['detail']

    def test_check_last_scrape_success(self, db_session):
        status = ServiceStatus(
            last_scrape=datetime.now(),
            last_scrape_status='success',
            commits_added=5
        )
        db_session.add(status)
        db_session.commit()

        checker = HealthChecker(db_session)
        res = checker.check_last_scrape()
        assert res['passed'] is True
        assert 'commits' in res['detail']

    def test_check_last_scrape_error(self, db_session):
        status = ServiceStatus(
            last_scrape=datetime.now(),
            last_scrape_status='error',
            error_message='Scraper timed out'
        )
        db_session.add(status)
        db_session.commit()

        checker = HealthChecker(db_session)
        res = checker.check_last_scrape()
        assert res['passed'] is False
        assert 'failed: Scraper timed out' in res['detail']

    def test_check_last_scrape_stale(self, db_session):
        status = ServiceStatus(
            last_scrape=datetime.now() - timedelta(minutes=80),
            last_scrape_status='success',
            commits_added=3
        )
        db_session.add(status)
        db_session.commit()

        checker = HealthChecker(db_session)
        res = checker.check_last_scrape()
        assert res['passed'] is False
        assert 'No scrapes in' in res['detail']

    def test_full_health_check(self, db_session):
        checker = HealthChecker(db_session)
        res = checker.full_health_check()
        assert res['status'] == 'healthy'
        assert res['healthy'] is True
        assert len(res['checks']) == 2

    def test_cli_status(self, seeded_db_session, monkeypatch):
        # Patch get_session to return our seeded_db_session fixture
        monkeypatch.setattr("gitflow.cli.commands.status.get_session", lambda: seeded_db_session)

        runner = CliRunner()
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert 'HEALTHY' in result.output
