import pytest
from click.testing import CliRunner
from src.gitflow.cli.main import cli


class TestCliCommands:

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_cli_help(self, runner):
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'GitFlow' in result.output

    def test_cli_add_command_no_path(self, runner):
        result = runner.invoke(cli, ['add'])
        assert result.exit_code != 0
        assert 'Missing argument' in result.output

    def test_cli_repos_empty(self, runner):
        result = runner.invoke(cli, ['repos'])
        assert result.exit_code == 0

    def test_cli_report_help(self, runner):
        result = runner.invoke(cli, ['report', '--help'])
        assert result.exit_code == 0
        assert 'Reporting commands' in result.output

    def test_cli_report_daily(self, runner):
        result = runner.invoke(cli, ['report', 'daily'])
        assert result.exit_code == 0

    def test_cli_report_streaks(self, runner):
        result = runner.invoke(cli, ['report', 'streaks'])
        assert result.exit_code == 0

    def test_cli_report_patterns(self, runner):
        result = runner.invoke(cli, ['report', 'patterns'])
        assert result.exit_code == 0

    def test_cli_export_csv(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['export', '--format', 'csv', '--output', 'test_export', '--days', '30'])
            assert result.exit_code == 0

    def test_cli_export_json(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ['export', '--format', 'json', '--output', 'test_export', '--days', '30'])
            assert result.exit_code == 0

    def test_cli_history(self, runner):
        result = runner.invoke(cli, ['history', '--days', '7'])
        assert result.exit_code == 0

    def test_cli_scan_no_repos(self, runner):
        result = runner.invoke(cli, ['scan'])
        assert result.exit_code == 0

    def test_cli_report_monthly(self, runner):
        result = runner.invoke(cli, ['report', 'monthly'])
        assert result.exit_code == 0

    def test_cli_report_weekly(self, runner):
        result = runner.invoke(cli, ['report', 'weekly', '--weeks', '2'])
        assert result.exit_code == 0

    def test_cli_version(self, runner):
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '1.0.0' in result.output
