import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch
from pathlib import Path
from gitflow.cli.main import cli
import gitflow.config

class TestCliCommands:

    @pytest.fixture(autouse=True)
    def mock_config_and_db(self, tmp_path, seeded_db_session, monkeypatch):
        # Isolate config file in a temp path
        temp_config = tmp_path / "config.yml"
        gitflow.config.Config._config_path = temp_config
        gitflow.config.Config._config = gitflow.config.DEFAULT_CONFIG.copy()

        # Mock database session across CLI commands
        monkeypatch.setattr("gitflow.cli.main.get_session", lambda: seeded_db_session)
        monkeypatch.setattr("gitflow.db.get_session", lambda: seeded_db_session)

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_help(self, runner):
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'GitFlow' in result.output

    def test_cli_version(self, runner):
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output

    def test_cli_add_command_no_path(self, runner):
        result = runner.invoke(cli, ['add'])
        assert result.exit_code != 0
        assert 'Missing argument' in result.output

    def test_cli_add_valid(self, runner, monkeypatch):
        mock_scraper = MagicMock()
        mock_scraper.add_repository.return_value = True
        monkeypatch.setattr("gitflow.cli.main.GitScraper", lambda sess: mock_scraper)

        result = runner.invoke(cli, ['add', str(Path.cwd())])
        assert result.exit_code == 0
        assert 'Repository added' in result.output

    def test_cli_add_invalid(self, runner, monkeypatch):
        mock_scraper = MagicMock()
        mock_scraper.add_repository.return_value = False
        monkeypatch.setattr("gitflow.cli.main.GitScraper", lambda sess: mock_scraper)

        result = runner.invoke(cli, ['add', str(Path.cwd())])
        assert result.exit_code == 0
        assert 'Failed to add repository' in result.output

    def test_cli_scan_with_repos(self, runner, temp_git_repo, seeded_db_session, monkeypatch):
        # Let's seed a real Repository path that actually exists so scan does not fail path existence check
        from gitflow.models import Repository
        repo = seeded_db_session.query(Repository).first()
        repo.path = str(temp_git_repo)
        seeded_db_session.commit()

        mock_scraper = MagicMock()
        mock_scraper.scan_commits_since.return_value = 3
        monkeypatch.setattr("gitflow.cli.main.GitScraper", lambda sess: mock_scraper)

        result = runner.invoke(cli, ['scan', '--since', '7days'])
        assert result.exit_code == 0
        assert 'Total: 3 new commits' in result.output

    def test_cli_scan_invalid_since(self, runner):
        result = runner.invoke(cli, ['scan', '--since', 'invalid_date'])
        assert result.exit_code == 0
        assert 'Invalid date format' in result.output

    def test_cli_history(self, runner):
        result = runner.invoke(cli, ['history', '--days', '7'])
        assert result.exit_code == 0
        assert 'Recent Commits' in result.output

    def test_cli_repos(self, runner):
        result = runner.invoke(cli, ['repos'])
        assert result.exit_code == 0
        assert 'Tracked Repositories' in result.output

    def test_cli_report_daily(self, runner):
        result = runner.invoke(cli, ['report', 'daily'])
        assert result.exit_code == 0
        assert 'Daily Report' in result.output

    def test_cli_report_weekly(self, runner):
        result = runner.invoke(cli, ['report', 'weekly', '--weeks', '2'])
        assert result.exit_code == 0

    def test_cli_report_streaks(self, runner):
        result = runner.invoke(cli, ['report', 'streaks'])
        assert result.exit_code == 0
        assert 'Commit Streaks' in result.output

    def test_cli_report_patterns(self, runner):
        result = runner.invoke(cli, ['report', 'patterns'])
        assert result.exit_code == 0
        assert 'Commit Patterns' in result.output

    def test_cli_report_monthly(self, runner):
        result = runner.invoke(cli, ['report', 'monthly'])
        assert result.exit_code == 0
        assert 'Monthly Report' in result.output

    def test_cli_init_service(self, runner, monkeypatch):
        mock_service = MagicMock()
        monkeypatch.setattr("gitflow.scheduler.background_service.BackgroundService", lambda: mock_service)

        result = runner.invoke(cli, ['init-service'])
        assert result.exit_code == 0
        assert 'Background service started' in result.output
        mock_service.start.assert_called_once()

    def test_cli_dashboard(self, runner, monkeypatch):
        mock_run = MagicMock()
        monkeypatch.setattr("uvicorn.run", mock_run)

        result = runner.invoke(cli, ['dashboard', '--port', '8500'])
        assert result.exit_code == 0
        assert 'Starting dashboard on http://localhost:8500' in result.output
        mock_run.assert_called_once_with('src.gitflow.dashboard.api.main:app', host='0.0.0.0', port=8500, reload=False)

    def test_cli_export_csv(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['export', '--format', 'csv', '--output', 'test_export', '--days', '30'])
            assert result.exit_code == 0
            assert 'Exported' in result.output
            assert Path('test_export.csv').exists()

    def test_cli_export_json(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['export', '--format', 'json', '--output', 'test_export', '--days', '30'])
            assert result.exit_code == 0
            assert 'Exported' in result.output
            assert Path('test_export.json').exists()

    def test_cli_export_markdown(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['export', '--format', 'markdown', '--output', 'test_export', '--days', '30'])
            assert result.exit_code == 0
            assert 'Exported' in result.output
            assert Path('test_export.markdown').exists()

    def test_cli_config_show(self, runner):
        result = runner.invoke(cli, ['config-show'])
        assert result.exit_code == 0
        assert 'GitFlow Configuration' in result.output

    def test_cli_config_set(self, runner):
        result = runner.invoke(cli, ['config-set', 'gitflow.scrape_interval_hours', '2'])
        assert result.exit_code == 0
        assert 'Set gitflow.scrape_interval_hours = 2' in result.output
        assert gitflow.config.Config.get('gitflow.scrape_interval_hours') == 2

    def test_cli_config_reset(self, runner):
        result = runner.invoke(cli, ['config-reset'])
        assert result.exit_code == 0
        assert 'Configuration reset' in result.output

    def test_cli_token_generate(self, runner, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.auth.generate_token", lambda: "test_token_123")
        result = runner.invoke(cli, ['token', 'generate'])
        assert result.exit_code == 0
        assert 'test_token_123' in result.output

    def test_cli_token_show(self, runner, monkeypatch):
        monkeypatch.setattr("gitflow.dashboard.api.auth.get_token", lambda: "existing_token")
        result = runner.invoke(cli, ['token', 'show'])
        assert result.exit_code == 0
        assert 'existing_token' in result.output

    def test_cli_token_revoke(self, runner, monkeypatch):
        mock_revoke = MagicMock()
        monkeypatch.setattr("gitflow.dashboard.api.auth.revoke_token", mock_revoke)
        result = runner.invoke(cli, ['token', 'revoke'])
        assert result.exit_code == 0
        assert 'API token revoked' in result.output
        mock_revoke.assert_called_once()

    @patch('rich.prompt.Prompt.ask')
    @patch('rich.prompt.Confirm.ask')
    def test_cli_setup(self, mock_confirm, mock_prompt, runner, monkeypatch, temp_git_repo):
        mock_prompt.side_effect = [
            str(temp_git_repo), # Repository path
            "done", # Repository path
            "http://slack", # Slack webhook
            "test@gmail.com", # Email address
            "app_password", # Gmail app password
            "85", # Productivity threshold
            "light", # Theme
        ]
        
        mock_confirm.side_effect = [
            True, # Configure Slack?
            True, # Configure Email?
            True, # Use Gmail?
            True, # Start background service?
        ]

        mock_service = MagicMock()
        monkeypatch.setattr("gitflow.scheduler.background_service.BackgroundService", lambda: mock_service)

        result = runner.invoke(cli, ['setup'])
        assert result.exit_code == 0
        assert 'Setup complete!' in result.output
        
        assert gitflow.config.Config.get('notifications.slack_webhook') == "http://slack"
        assert gitflow.config.Config.get('notifications.email_address') == "test@gmail.com"
        assert gitflow.config.Config.get('analytics.productivity_threshold') == 85
        assert gitflow.config.Config.get('ui.theme') == "light"
