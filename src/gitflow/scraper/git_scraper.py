from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import git
from git import Repo
from git.exc import InvalidGitRepositoryError
import logging

logger = logging.getLogger(__name__)


class GitScraper:
    def __init__(self, db_session):
        self.db = db_session
        self.repos: List[Path] = []

    def add_repository(self, repo_path: Path) -> bool:
        try:
            repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            logger.error(f"Invalid git repository at {repo_path}")
            return False
        except Exception as e:
            logger.error(f"Error accessing repo at {repo_path}: {e}")
            return False

        try:
            if repo.remotes:
                repo.remotes.origin.fetch()
        except (IndexError, AttributeError):
            pass
        except Exception as e:
            logger.warning(f"Could not fetch from remote for {repo_path}: {e}")

        from src.gitflow.models import Repository

        existing = self.db.query(Repository).filter_by(path=str(repo_path)).first()
        if existing:
            return True

        try:
            remote_url = repo.remotes.origin.url
        except (IndexError, AttributeError):
            remote_url = None

        try:
            default_branch = repo.active_branch.name
        except (TypeError, ValueError):
            default_branch = 'main'

        repository = Repository(
            path=str(repo_path),
            name=repo_path.name,
            remote_url=remote_url,
            default_branch=default_branch
        )

        self.db.add(repository)
        self.db.commit()

        logger.info(f"Added repository: {repo_path}")
        return True

    def scan_commits_since(self, repo_path: Path, since: datetime) -> int:
        from src.gitflow.models import Repository, Commit, CommitFile

        repo = Repo(repo_path)
        repository = self.db.query(Repository).filter_by(path=str(repo_path)).first()

        if not repository:
            logger.warning(f"Repository {repo_path} not tracked")
            return 0

        commits_added = 0

        for branch in repo.heads:
            try:
                commits = list(repo.iter_commits(
                    branch,
                    since=since,
                    reverse=True
                ))

                for commit_obj in commits:
                    existing = self.db.query(Commit).filter_by(
                        commit_hash=commit_obj.hexsha
                    ).first()
                    if existing:
                        continue

                    commit = self._parse_commit(commit_obj, repository, branch.name)
                    self.db.add(commit)
                    self.db.flush()

                    files = self._parse_files(commit_obj, commit)
                    for file in files:
                        self.db.add(file)

                    commits_added += 1

            except Exception as e:
                logger.error(f"Error processing branch {branch.name}: {e}")

        self.db.commit()
        logger.info(f"Added {commits_added} commits from {repo_path.name}")
        return commits_added

    def _parse_commit(self, commit_obj: git.Commit, repository, branch: str):
        from src.gitflow.models import Commit

        stats = commit_obj.stats.total
        insertions = stats.get('insertions', 0)
        deletions = stats.get('deletions', 0)

        commit = Commit(
            repo_id=repository.id,
            commit_hash=commit_obj.hexsha,
            author=commit_obj.author.name,
            author_email=commit_obj.author.email,
            committer=commit_obj.committer.name,
            committer_email=commit_obj.committer.email,
            message=commit_obj.message,
            message_summary=commit_obj.message.split('\n')[0],
            committed_date=datetime.fromtimestamp(commit_obj.committed_date),
            committed_unix=commit_obj.committed_date,
            files_changed=len(commit_obj.stats.files),
            insertions=insertions,
            deletions=deletions,
            net_change=insertions - deletions,
            is_merge=len(commit_obj.parents) > 1,
            branch=branch
        )

        return commit

    def _parse_files(self, commit_obj: git.Commit, commit) -> List:
        from src.gitflow.models import CommitFile

        files = []

        for filename, diff_info in commit_obj.stats.files.items():
            file = CommitFile(
                commit_id=commit.id,
                file_path=filename,
                status=self._get_file_status(commit_obj, filename),
                insertions=diff_info.get('additions', 0),
                deletions=diff_info.get('deletions', 0)
            )
            files.append(file)

        return files

    def _get_file_status(self, commit_obj: git.Commit, filename: str) -> str:
        if len(commit_obj.parents) == 0:
            return 'added'

        parent = commit_obj.parents[0]

        if filename in parent.stats.files:
            return 'modified'
        else:
            return 'added'

    def get_tracked_repos(self) -> List[Path]:
        from src.gitflow.models import Repository
        repos = self.db.query(Repository).filter_by(tracked=True).all()
        return [Path(r.path) for r in repos]

    def scan_all_repos(self) -> int:
        repos = self.get_tracked_repos()
        since = datetime.now() - timedelta(days=1)

        total_commits = 0
        for repo_path in repos:
            try:
                commits = self.scan_commits_since(repo_path, since)
                total_commits += commits
            except Exception as e:
                logger.error(f"Error scanning {repo_path}: {e}")

        return total_commits
