from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from functools import wraps
import git
from git import Repo
from git.exc import InvalidGitRepositoryError, GitCommandError
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
        except GitCommandError as e:
            logger.warning(f"Git command error for {repo_path}: {e}")
        except Exception as e:
            logger.warning(f"Could not fetch from remote for {repo_path}: {e}")

        from gitflow.models import Repository

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

    def scan_commits_since(self, repo_path: Path, since: datetime, max_commits: int = 10000) -> int:
        from gitflow.models import Repository, Commit, CommitFile

        try:
            repo = Repo(repo_path)
        except InvalidGitRepositoryError:
            logger.error(f"Invalid git repository at {repo_path}")
            return 0
        except Exception as e:
            logger.error(f"Error opening repo at {repo_path}: {e}")
            return 0

        try:
            repository = self.db.query(Repository).filter_by(path=str(repo_path)).first()
        except Exception as e:
            logger.error(f"Database error querying repository {repo_path}: {e}")
            return 0

        if not repository:
            logger.warning(f"Repository {repo_path} not tracked")
            return 0

        try:
            if not list(repo.heads):
                logger.warning(f"Repository {repo_path} has no branches")
                return 0
        except Exception as e:
            logger.error(f"Error checking branches for {repo_path}: {e}")
            return 0

        commits_added = 0
        affected_dates = set()

        for branch in repo.heads:
            try:
                commits = list(repo.iter_commits(
                    branch,
                    since=since,
                    reverse=True,
                    max_count=max_commits
                ))

                for commit_obj in commits:
                    try:
                        existing = self.db.query(Commit).filter_by(
                            commit_hash=commit_obj.hexsha
                        ).first()
                        if existing:
                            continue

                        commit = self._parse_commit(commit_obj, repository, branch.name)
                        self.db.add(commit)
                        self.db.flush()
                        affected_dates.add(commit.committed_date.date())

                        files = self._parse_files(commit_obj, commit)
                        for file in files:
                            self.db.add(file)

                        commits_added += 1

                        if commits_added >= max_commits:
                            logger.warning(f"Reached max_commits limit ({max_commits}) for {repo_path.name}")
                            break

                    except Exception as e:
                        logger.error(f"Error parsing commit {commit_obj.hexsha[:8]}: {e}")
                        continue

            except GitCommandError as e:
                logger.error(f"Git error processing branch {branch.name} of {repo_path.name}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing branch {branch.name}: {e}")
                continue

        try:
            self.db.commit()
        except Exception as e:
            logger.error(f"Database commit error for {repo_path}: {e}")
            self.db.rollback()
            return 0

        if affected_dates:
            try:
                from gitflow.models import DailyStat, WeeklyStat, MonthlyStat
                self.db.query(DailyStat).filter(
                    DailyStat.date.in_(list(affected_dates))
                ).delete(synchronize_session=False)

                week_starts = set((d - timedelta(days=d.weekday())) for d in affected_dates)
                self.db.query(WeeklyStat).filter(
                    WeeklyStat.week_start.in_(list(week_starts))
                ).delete(synchronize_session=False)

                month_keys = set((d.year, d.month) for d in affected_dates)
                for yr, mo in month_keys:
                    self.db.query(MonthlyStat).filter_by(year=yr, month=mo).delete(synchronize_session=False)

                self.db.commit()
            except Exception as e:
                logger.warning(f"Failed to invalidate DailyStat cache: {e}")

        logger.info(f"Added {commits_added} commits from {repo_path.name}")
        return commits_added

    def _parse_commit(self, commit_obj: git.Commit, repository, branch: str):
        from gitflow.models import Commit

        try:
            stats = commit_obj.stats.total
            insertions = stats.get('insertions', 0)
            deletions = stats.get('deletions', 0)
        except Exception:
            insertions = 0
            deletions = 0

        author_name = commit_obj.author.name or 'Unknown'
        author_email = commit_obj.author.email or ''
        committer_name = commit_obj.committer.name or ''
        committer_email = commit_obj.committer.email or ''

        message = commit_obj.message or ''
        message_summary = message.split('\n')[0] if message else ''

        commit = Commit(
            repo_id=repository.id,
            commit_hash=commit_obj.hexsha,
            author=author_name,
            author_email=author_email,
            committer=committer_name,
            committer_email=committer_email,
            message=message,
            message_summary=message_summary,
            committed_date=datetime.fromtimestamp(commit_obj.committed_date),
            committed_unix=commit_obj.committed_date,
            files_changed=len(commit_obj.stats.files) if hasattr(commit_obj.stats, 'files') else 0,
            insertions=insertions,
            deletions=deletions,
            net_change=insertions - deletions,
            is_merge=len(commit_obj.parents) > 1,
            branch=branch
        )

        return commit

    def _parse_files(self, commit_obj: git.Commit, commit) -> List:
        from gitflow.models import CommitFile

        files = []

        try:
            for filename, diff_info in commit_obj.stats.files.items():
                file = CommitFile(
                    commit_id=commit.id,
                    file_path=filename,
                    status=self._get_file_status(commit_obj, filename),
                    insertions=diff_info.get('additions', 0),
                    deletions=diff_info.get('deletions', 0)
                )
                files.append(file)
        except Exception as e:
            logger.warning(f"Error parsing files for commit {commit.commit_hash[:8]}: {e}")

        return files

    def _get_file_status(self, commit_obj: git.Commit, filename: str) -> str:
        try:
            if len(commit_obj.parents) == 0:
                return 'added'

            parent = commit_obj.parents[0]
            if filename in parent.stats.files:
                return 'modified'
            else:
                return 'added'
        except Exception:
            return 'modified'

    def _is_merge_commit(self, commit_obj: git.Commit) -> bool:
        return len(commit_obj.parents) > 1

    def _is_revert_commit(self, commit_obj: git.Commit) -> bool:
        try:
            message = commit_obj.message or ''
            return message.startswith('Revert ')
        except Exception:
            return False

    def _is_squash_commit(self, commit_obj: git.Commit) -> bool:
        try:
            message = commit_obj.message or ''
            return len(commit_obj.parents) > 2 or '# This is a combination' in message
        except Exception:
            return False

    def get_tracked_repos(self) -> List[Path]:
        from gitflow.models import Repository
        try:
            repos = self.db.query(Repository).filter_by(tracked=True).all()
            return [Path(r.path) for r in repos if Path(r.path).exists()]
        except Exception as e:
            logger.error(f"Error getting tracked repos: {e}")
            return []

    def scan_all_repos(self, since: Optional[datetime] = None) -> int:
        repos = self.get_tracked_repos()
        if since is None:
            since = datetime.now() - timedelta(days=1)

        total_commits = 0
        for repo_path in repos:
            try:
                if not repo_path.exists():
                    logger.warning(f"Repository path no longer exists: {repo_path}")
                    continue
                commits = self.scan_commits_since(repo_path, since)
                total_commits += commits
            except GitCommandError as e:
                logger.error(f"Git error scanning {repo_path}: {e}")
            except ConnectionError as e:
                logger.error(f"Network error scanning {repo_path}: {e}")
            except Exception as e:
                logger.error(f"Error scanning {repo_path}: {e}")

        return total_commits

    def _handle_network_error(self, repo_path: Path, error: Exception) -> None:
        logger.error(f"Network error for {repo_path}: {error}")
        logger.info(f"Skipping {repo_path} due to network error")

    def _handle_invalid_repo(self, repo_path: Path) -> bool:
        logger.warning(f"Repository no longer valid: {repo_path}")
        return False
