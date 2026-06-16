import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from datetime import datetime
from gitflow.scheduler.background_service import BackgroundService
from gitflow.models import ServiceStatus
from gitflow.config import Config

class TestBackgroundService:

    def test_parse_time(self):
        service = BackgroundService()
        assert service._parse_time("08:30") == (8, 30)
        assert service._parse_time("00:00") == (0, 0)
        assert service._parse_time("invalid") == (0, 1)

    @patch('gitflow.scheduler.background_service.BackgroundScheduler')
    def test_start_stop(self, mock_scheduler_class):
        mock_sched = MagicMock()
        mock_scheduler_class.return_value = mock_sched
        mock_sched.running = True

        service = BackgroundService()
        service.start()

        assert mock_sched.add_job.call_count == 3
        mock_sched.start.assert_called_once()

        service.stop()
        mock_sched.shutdown.assert_called_once()

    def test_scrape_all_repos_success(self, db_session, monkeypatch):
        monkeypatch.setattr("gitflow.scheduler.background_service.get_session", lambda: db_session)
        
        mock_scraper = MagicMock()
        mock_scraper.scan_all_repos.return_value = 5
        monkeypatch.setattr("gitflow.scraper.git_scraper.GitScraper", lambda sess: mock_scraper)

        service = BackgroundService()
        service._scrape_all_repos()

        status = db_session.query(ServiceStatus).first()
        assert status is not None
        assert status.last_scrape_status == 'success'
        assert status.commits_added == 5
        assert status.error_message is None

    def test_scrape_all_repos_failure(self, db_session, monkeypatch):
        monkeypatch.setattr("gitflow.scheduler.background_service.get_session", lambda: db_session)
        
        mock_scraper = MagicMock()
        mock_scraper.scan_all_repos.side_effect = ValueError("Database connection lost")
        monkeypatch.setattr("gitflow.scraper.git_scraper.GitScraper", lambda sess: mock_scraper)

        service = BackgroundService()
        service._scrape_all_repos()

        status = db_session.query(ServiceStatus).first()
        assert status is not None
        assert status.last_scrape_status == 'error'
        assert status.commits_added == 0
        assert "Database connection lost" in status.error_message

    def test_calculate_daily_stats(self, db_session, monkeypatch):
        monkeypatch.setattr("gitflow.scheduler.background_service.get_session", lambda: db_session)
        
        mock_analytics = MagicMock()
        mock_analytics.get_daily_stats.return_value = {'commit_count': 10}
        monkeypatch.setattr("gitflow.analytics.analytics_engine.AnalyticsEngine", lambda sess: mock_analytics)

        service = BackgroundService()
        service._calculate_daily_stats()
        
        mock_analytics.get_daily_stats.assert_called_once()
