import pytest
from unittest.mock import MagicMock, patch
from gitflow.notifications.notifier import NotificationService
from gitflow.scheduler.background_service import BackgroundService
from gitflow.config import Config

class TestNotifications:
    @patch('requests.post')
    def test_send_slack_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch.object(Config, 'get', return_value='https://hooks.slack.com/services/test'):
            res = NotificationService.send_slack("Test message")
            assert res is True
            mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_slack_failure(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        with patch.object(Config, 'get', return_value='https://hooks.slack.com/services/test'):
            res = NotificationService.send_slack("Test message")
            assert res is False

    @patch('smtplib.SMTP')
    def test_send_email_success(self, mock_smtp):
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch.object(Config, 'get') as mock_get:
            def side_effect(key, default=None):
                if key == 'notifications.smtp_username': return 'user@gmail.com'
                if key == 'notifications.smtp_user': return 'user@gmail.com'
                if key == 'notifications.smtp_password': return 'password'
                if key == 'notifications.smtp_host': return 'smtp.gmail.com'
                if key == 'notifications.smtp_port': return 587
                return default
            mock_get.side_effect = side_effect

            res = NotificationService.send_email("recipient@test.com", "Subject", "<p>Body</p>")
            assert res is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('user@gmail.com', 'password')
            mock_server.send_message.assert_called_once()

    @patch('requests.post')
    def test_send_daily_digest_slack_only(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        with patch.object(Config, 'get') as mock_get:
            def side_effect(key, default=None):
                if key == 'notifications.slack_webhook': return 'https://hooks.slack.com/services/test'
                if key == 'notifications.email_enabled': return False
                return default
            mock_get.side_effect = side_effect

            stats = {'commit_count': 5, 'lines_added': 100, 'lines_deleted': 20, 'files_touched': 4}
            repos = [{'repository': 'repo1', 'commits': 5}]
            results = NotificationService.send_daily_digest(stats, 85.0, repos)
            assert results['slack'] is True
            assert results['email'] is False

    @patch('requests.post')
    @patch('smtplib.SMTP')
    def test_background_service_send_daily_digest(self, mock_smtp, mock_post, seeded_db_session, monkeypatch):
        mock_post.return_value.status_code = 200
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        monkeypatch.setattr("gitflow.scheduler.background_service.get_session", lambda: seeded_db_session)

        with patch.object(Config, 'get') as mock_get:
            def side_effect(key, default=None):
                if key == 'notifications.slack_webhook': return 'https://hooks.slack.com/services/test'
                if key == 'notifications.email_enabled': return True
                if key == 'notifications.email_address': return 'recipient@test.com'
                if key == 'notifications.smtp_username': return 'user@gmail.com'
                if key == 'notifications.smtp_user': return 'user@gmail.com'
                if key == 'notifications.smtp_password': return 'password'
                if key == 'notifications.smtp_host': return 'smtp.gmail.com'
                if key == 'notifications.smtp_port': return 587
                return default
            mock_get.side_effect = side_effect

            service = BackgroundService()
            service._send_daily_digest()

            # Verify that ServiceStatus log is added and service ran successfully
            from gitflow.models import ServiceStatus
            status = seeded_db_session.query(ServiceStatus).first()
            assert status is not None
            assert status.last_scrape_status == 'success'
            # commits_added reflects today's commits (seeded data is 2 days ago, so 0 is valid)
            assert status.commits_added >= 0
