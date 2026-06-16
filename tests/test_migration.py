import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from gitflow.cli.main import cli

class TestMigrationCli:
    @patch('subprocess.run')
    def test_migration_history(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "147a729ba08a (head), initial_schema"
        mock_run.return_value = mock_result

        runner = CliRunner()
        result = runner.invoke(cli, ['migration', 'history'])
        assert result.exit_code == 0
        assert '147a729ba08a' in result.output
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_migration_create(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Generated revision 2390aefd123b"
        mock_run.return_value = mock_result

        runner = CliRunner()
        result = runner.invoke(cli, ['migration', 'create', 'add_column'])
        assert result.exit_code == 0
        assert 'Generated revision' in result.output
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_migration_upgrade(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Running upgrade -> 147a729ba08a"
        mock_run.return_value = mock_result

        runner = CliRunner()
        result = runner.invoke(cli, ['migration', 'upgrade'])
        assert result.exit_code == 0
        assert 'Running upgrade' in result.output
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_migration_downgrade(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Running downgrade -> base"
        mock_run.return_value = mock_result

        runner = CliRunner()
        result = runner.invoke(cli, ['migration', 'downgrade'])
        assert result.exit_code == 0
        assert 'Running downgrade' in result.output
        mock_run.assert_called_once()
