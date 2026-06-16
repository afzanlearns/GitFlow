import pytest
from pathlib import Path
from datetime import datetime
from src.gitflow.scraper.git_scraper import GitScraper
from src.gitflow.models import Commit, Repository


class TestGitScraper:

    def test_add_repository_valid(self, db_session, temp_git_repo):
        scraper = GitScraper(db_session)
        result = scraper.add_repository(temp_git_repo)
        assert result is True

        repo = db_session.query(Repository).filter_by(path=str(temp_git_repo)).first()
        assert repo is not None
        assert repo.name == temp_git_repo.name

    def test_add_repository_invalid(self, db_session):
        scraper = GitScraper(db_session)
        result = scraper.add_repository(Path('/nonexistent/path'))
        assert result is False

    def test_add_repository_duplicate(self, db_session, temp_git_repo):
        scraper = GitScraper(db_session)
        first = scraper.add_repository(temp_git_repo)
        second = scraper.add_repository(temp_git_repo)
        assert first is True
        assert second is True

        count = db_session.query(Repository).filter_by(path=str(temp_git_repo)).count()
        assert count == 1

    def test_scan_commits_deduplication(self, db_session, temp_git_repo):
        scraper = GitScraper(db_session)
        scraper.add_repository(temp_git_repo)

        since = datetime(2024, 1, 1)
        first_scan = scraper.scan_commits_since(temp_git_repo, since)
        assert first_scan == 5

        second_scan = scraper.scan_commits_since(temp_git_repo, since)
        assert second_scan == 0

        total = db_session.query(Commit).count()
        assert total == 5

    def test_parse_commit_metadata(self, db_session, temp_git_repo):
        scraper = GitScraper(db_session)
        scraper.add_repository(temp_git_repo)

        since = datetime(2024, 1, 1)
        scraper.scan_commits_since(temp_git_repo, since)

        commits = db_session.query(Commit).order_by(Commit.committed_date).all()
        assert len(commits) == 5

        first = commits[0]
        assert first.author == 'Test User'
        assert first.author_email == 'test@test.com'
        assert first.message_summary == 'feat: commit 0 - testing'
        assert first.branch == 'master'

    def test_parse_commit_files(self, db_session, temp_git_repo):
        scraper = GitScraper(db_session)
        scraper.add_repository(temp_git_repo)

        since = datetime(2024, 1, 1)
        scraper.scan_commits_since(temp_git_repo, since)

        commits = db_session.query(Commit).all()
        for c in commits:
            assert c.files_changed >= 1
            assert len(c.files) == c.files_changed
            for f in c.files:
                assert f.file_path is not None
                assert f.status in ('added', 'modified')

    def test_get_tracked_repos(self, db_session, temp_git_repo, temp_repo_no_commits):
        scraper = GitScraper(db_session)
        scraper.add_repository(temp_git_repo)
        scraper.add_repository(temp_repo_no_commits)

        repos = scraper.get_tracked_repos()
        assert len(repos) == 2
        assert temp_git_repo in repos
        assert temp_repo_no_commits in repos

    def test_scan_all_repos(self, db_session, temp_git_repo, temp_repo_no_commits):
        scraper = GitScraper(db_session)
        scraper.add_repository(temp_git_repo)
        scraper.add_repository(temp_repo_no_commits)

        total = scraper.scan_all_repos()
        assert total > 0
        assert isinstance(total, int)

    def test_add_repository_tracks_branch(self, db_session, temp_git_repo):
        scraper = GitScraper(db_session)
        scraper.add_repository(temp_git_repo)

        repo = db_session.query(Repository).filter_by(path=str(temp_git_repo)).first()
        assert repo.default_branch == 'master'
        assert repo.remote_url is None
