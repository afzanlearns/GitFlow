# GitFlow - Complete Build Guide & Agent Prompt

**Status: CLI-based (Python Click) + Web Dashboard (React/FastAPI)**

---

## Overview

GitFlow is a comprehensive Git analytics and commit tracking tool that scrapes commit data, calculates productivity metrics, detects patterns, and provides beautiful visualizations. The core is CLI-based for scriptability, with an optional web dashboard for analytics visualization.

**Why CLI + Dashboard:** CLI captures commits locally and runs on schedule, dashboard provides beautiful visualizations without requiring CLI interactions. Both are optional—CLI works standalone.

---

## Architecture Overview

```
GitFlow System
├─ Core CLI (Python Click)
│  ├─ Commit scraper (watches git repos)
│  ├─ Daily/weekly/monthly reports
│  ├─ Commit statistics
│  ├─ Streak tracking
│  └─ Scheduled scraping (background service)
│
├─ Data Processing
│  ├─ Git repository walker
│  ├─ Commit parser
│  ├─ Diff analyzer
│  ├─ Analytics engine
│  └─ Anomaly detection
│
├─ Database Layer (SQLite)
│  ├─ Commits
│  ├─ Repositories
│  ├─ Files touched
│  ├─ Daily stats (cache)
│  └─ Analytics data
│
├─ Background Service
│  ├─ Scheduled commit scraping
│  ├─ Analytics calculation
│  ├─ Notification dispatch
│  └─ Database maintenance
│
└─ Web Dashboard (Optional)
   ├─ FastAPI backend
   ├─ WebSocket for real-time updates
   ├─ React frontend
   ├─ D3/Recharts visualizations
   └─ Search and filtering
```

---

## Technology Stack

```
Core & Scraper:
  • Python 3.10+
  • GitPython (Git repository access)
  • Click (CLI framework)
  • Rich (terminal formatting)
  • SQLAlchemy (ORM)
  • SQLite (local database)
  • APScheduler (background jobs)
  • python-dotenv (configuration)

Analytics:
  • Pandas (data manipulation)
  • NumPy (statistical analysis)
  • Scikit-learn (anomaly detection)

Dashboard (Optional):
  • FastAPI (async API)
  • React 18+
  • D3.js / Recharts (visualizations)
  • WebSockets (real-time updates)
  • Tailwind CSS

Notifications:
  • Plyer (system notifications)
  • Requests (webhooks/slack)
```

---

## Database Schema

```sql
CREATE TABLE repositories (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  remote_url TEXT,
  default_branch TEXT DEFAULT 'main',
  tracked BOOLEAN DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commits (
  id INTEGER PRIMARY KEY,
  repo_id INTEGER NOT NULL,
  commit_hash TEXT UNIQUE NOT NULL,
  author TEXT NOT NULL,
  author_email TEXT,
  committer TEXT,
  committer_email TEXT,
  message TEXT NOT NULL,
  message_summary TEXT, -- First line only
  committed_date TIMESTAMP NOT NULL,
  committed_unix BIGINT,
  files_changed INTEGER,
  insertions INTEGER,
  deletions INTEGER,
  net_change INTEGER,
  is_merge BOOLEAN DEFAULT 0,
  branch TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (repo_id) REFERENCES repositories(id),
  INDEX idx_date (committed_date),
  INDEX idx_author (author),
  INDEX idx_repo (repo_id)
);

CREATE TABLE commit_files (
  id INTEGER PRIMARY KEY,
  commit_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  status TEXT, -- 'added', 'modified', 'deleted'
  insertions INTEGER DEFAULT 0,
  deletions INTEGER DEFAULT 0,
  FOREIGN KEY (commit_id) REFERENCES commits(id)
);

CREATE TABLE daily_stats (
  id INTEGER PRIMARY KEY,
  date DATE UNIQUE,
  commit_count INTEGER DEFAULT 0,
  total_lines_added INTEGER DEFAULT 0,
  total_lines_deleted INTEGER DEFAULT 0,
  files_touched INTEGER DEFAULT 0,
  repos_worked_on INTEGER DEFAULT 0,
  top_language TEXT,
  avg_commit_message_length INTEGER,
  commit_convention_score FLOAT, -- 0-100
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE weekly_stats (
  id INTEGER PRIMARY KEY,
  week_start DATE,
  week_end DATE,
  commit_count INTEGER,
  total_lines_added INTEGER,
  total_lines_deleted INTEGER,
  avg_commits_per_day FLOAT,
  most_active_day TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(week_start)
);

CREATE TABLE monthly_stats (
  id INTEGER PRIMARY KEY,
  year INTEGER,
  month INTEGER,
  commit_count INTEGER,
  total_lines_added INTEGER,
  total_lines_deleted INTEGER,
  avg_commits_per_day FLOAT,
  productivity_score FLOAT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(year, month)
);

CREATE TABLE commit_streaks (
  id INTEGER PRIMARY KEY,
  author TEXT,
  start_date DATE,
  end_date DATE,
  days_count INTEGER,
  is_current BOOLEAN,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks_commits (
  id INTEGER PRIMARY KEY,
  commit_id INTEGER NOT NULL,
  task_id TEXT, -- For linking to task management tools
  task_title TEXT,
  project TEXT,
  FOREIGN KEY (commit_id) REFERENCES commits(id)
);

CREATE TABLE commit_annotations (
  id INTEGER PRIMARY KEY,
  commit_id INTEGER NOT NULL,
  label TEXT, -- 'refactor', 'bug-fix', 'feature', 'chore'
  score FLOAT, -- Confidence score (0-1)
  FOREIGN KEY (commit_id) REFERENCES commits(id)
);
```

---

## Core Implementation

### 1. Git Repository Scraper

```python
# src/scraper/git_scraper.py
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import git
from git import Repo
import logging

logger = logging.getLogger(__name__)

class GitScraper:
    def __init__(self, db_session):
        self.db = db_session
        self.repos: List[Path] = []
    
    def add_repository(self, repo_path: Path) -> bool:
        """Add repository to tracking"""
        try:
            repo = Repo(repo_path)
            repo.remotes.origin.fetch()  # Validate repo exists
        except Exception as e:
            logger.error(f"Invalid repo at {repo_path}: {e}")
            return False
        
        from models import Repository
        
        # Check if already tracked
        existing = self.db.query(Repository).filter_by(path=str(repo_path)).first()
        if existing:
            return True
        
        # Get remote URL
        try:
            remote_url = repo.remotes.origin.url
        except IndexError:
            remote_url = None
        
        repository = Repository(
            path=str(repo_path),
            name=repo_path.name,
            remote_url=remote_url,
            default_branch=repo.active_branch.name
        )
        
        self.db.add(repository)
        self.db.commit()
        
        logger.info(f"Added repository: {repo_path}")
        return True
    
    def scan_commits_since(self, repo_path: Path, since: datetime) -> int:
        """Scan commits since specific date"""
        from models import Repository, Commit, CommitFile
        from sqlalchemy import func
        
        repo = Repo(repo_path)
        repository = self.db.query(Repository).filter_by(path=str(repo_path)).first()
        
        if not repository:
            logger.warning(f"Repository {repo_path} not tracked")
            return 0
        
        # Get commits since date
        commits_added = 0
        
        for branch in repo.heads:
            try:
                commits = list(repo.iter_commits(
                    branch,
                    since=since,
                    reverse=True
                ))
                
                for commit_obj in commits:
                    # Skip if already in DB
                    existing = self.db.query(Commit).filter_by(
                        commit_hash=commit_obj.hexsha
                    ).first()
                    if existing:
                        continue
                    
                    # Parse commit
                    commit = self._parse_commit(commit_obj, repository, branch.name)
                    self.db.add(commit)
                    self.db.flush()
                    
                    # Parse touched files
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
        """Parse git commit into model"""
        from models import Commit
        
        # Count lines changed
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
        """Parse files touched in commit"""
        from models import CommitFile
        
        files = []
        
        for filename, diff_info in commit_obj.stats.files.items():
            file = CommitFile(
                commit_id=commit.id,
                file_path=filename,
                status=self._get_file_status(commit_obj, filename),
                insertions=diff_info['additions'],
                deletions=diff_info['deletions']
            )
            files.append(file)
        
        return files
    
    def _get_file_status(self, commit_obj: git.Commit, filename: str) -> str:
        """Determine file status (added/modified/deleted)"""
        # Simplified - could use more sophisticated diff analysis
        if len(commit_obj.parents) == 0:
            return 'added'  # Initial commit
        
        parent = commit_obj.parents[0]
        
        if filename in parent.stats.files:
            return 'modified'
        else:
            return 'added'
    
    def get_tracked_repos(self) -> List[Path]:
        """Get all tracked repositories"""
        from models import Repository
        repos = self.db.query(Repository).filter_by(tracked=True).all()
        return [Path(r.path) for r in repos]
    
    def scan_all_repos(self) -> int:
        """Scan all tracked repos for new commits"""
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
```

### 2. Analytics Engine

```python
# src/analytics/analytics_engine.py
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, and_, or_
import pandas as pd
import numpy as np

class AnalyticsEngine:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_daily_stats(self, target_date: date) -> Dict:
        """Calculate daily statistics"""
        from models import Commit, DailyStat
        from sqlalchemy import func
        
        # Check if cached
        cached = self.db.query(DailyStat).filter_by(date=target_date).first()
        if cached:
            return self._serialize_daily_stat(cached)
        
        # Calculate from commits
        commits = self.db.query(Commit).filter(
            func.date(Commit.committed_date) == target_date
        ).all()
        
        if not commits:
            return {
                'date': target_date.isoformat(),
                'commit_count': 0,
                'lines_added': 0,
                'lines_deleted': 0
            }
        
        commit_count = len(commits)
        total_added = sum(c.insertions for c in commits)
        total_deleted = sum(c.deletions for c in commits)
        files_touched = len(set(
            f.file_path for c in commits for f in c.files
        ))
        
        # Message analysis
        avg_msg_length = np.mean([len(c.message_summary) for c in commits])
        convention_score = self._score_commit_messages([c.message_summary for c in commits])
        
        # Cache result
        daily_stat = DailyStat(
            date=target_date,
            commit_count=commit_count,
            total_lines_added=total_added,
            total_lines_deleted=total_deleted,
            files_touched=files_touched,
            avg_commit_message_length=int(avg_msg_length),
            commit_convention_score=convention_score
        )
        
        self.db.add(daily_stat)
        self.db.commit()
        
        return self._serialize_daily_stat(daily_stat)
    
    def get_weekly_report(self, week_start: date) -> Dict:
        """Generate weekly report"""
        from models import Commit, WeeklyStat
        
        week_end = week_start + timedelta(days=6)
        
        # Check cache
        cached = self.db.query(WeeklyStat).filter_by(week_start=week_start).first()
        if cached:
            return self._serialize_weekly_stat(cached)
        
        commits = self.db.query(Commit).filter(
            and_(
                func.date(Commit.committed_date) >= week_start,
                func.date(Commit.committed_date) <= week_end
            )
        ).all()
        
        if not commits:
            return {'week_start': week_start.isoformat(), 'commits': 0}
        
        # Calculate metrics
        daily_commits = {}
        for commit in commits:
            day = commit.committed_date.date()
            daily_commits[day] = daily_commits.get(day, 0) + 1
        
        active_days = len(daily_commits)
        total_commits = len(commits)
        avg_per_day = total_commits / 7
        
        most_active_day = max(daily_commits, key=daily_commits.get) if daily_commits else None
        
        total_added = sum(c.insertions for c in commits)
        total_deleted = sum(c.deletions for c in commits)
        
        # Cache
        weekly = WeeklyStat(
            week_start=week_start,
            week_end=week_end,
            commit_count=total_commits,
            total_lines_added=total_added,
            total_lines_deleted=total_deleted,
            avg_commits_per_day=avg_per_day
        )
        
        self.db.add(weekly)
        self.db.commit()
        
        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'total_commits': total_commits,
            'active_days': active_days,
            'avg_per_day': round(avg_per_day, 1),
            'most_active_day': most_active_day.isoformat() if most_active_day else None,
            'lines_added': total_added,
            'lines_deleted': total_deleted,
            'daily_breakdown': {
                day.isoformat(): count
                for day, count in sorted(daily_commits.items())
            }
        }
    
    def get_productivity_score(self, target_date: date) -> float:
        """
        Calculate productivity score (0-100)
        Based on:
        - Commit frequency (30%)
        - Code quality (message format, size) (30%)
        - Diversity (files touched across repos) (20%)
        - Consistency (spreading commits across day) (20%)
        """
        from models import Commit
        
        commits = self.db.query(Commit).filter(
            func.date(Commit.committed_date) == target_date
        ).all()
        
        if not commits:
            return 0.0
        
        # Commit frequency score (30%)
        commit_count = len(commits)
        freq_score = min(100, (commit_count / 5) * 100) * 0.3
        
        # Code quality (30%)
        quality_score = self._score_commit_messages(
            [c.message_summary for c in commits]
        ) * 0.3
        
        # Diversity (20%)
        unique_files = len(set(
            f.file_path for c in commits for f in c.files
        ))
        diversity_score = min(100, (unique_files / 20) * 100) * 0.2
        
        # Consistency (20%)
        time_spread = self._calculate_time_spread(commits)
        consistency_score = time_spread * 0.2
        
        total_score = freq_score + quality_score + diversity_score + consistency_score
        return min(100, total_score)
    
    def get_current_streak(self, author: str) -> Tuple[int, bool]:
        """Get current commit streak for author"""
        from models import Commit
        from datetime import datetime
        
        today = datetime.now().date()
        current_streak = 0
        is_current = False
        
        # Walk backwards from today
        for i in range(365):
            check_date = today - timedelta(days=i)
            
            commits = self.db.query(Commit).filter(
                and_(
                    func.date(Commit.committed_date) == check_date,
                    Commit.author == author
                )
            ).count()
            
            if commits > 0:
                current_streak += 1
                if i == 0:
                    is_current = True
            else:
                if current_streak > 0:
                    break
        
        return current_streak, is_current
    
    def detect_patterns(self, days: int = 30) -> Dict:
        """Detect commit patterns"""
        from models import Commit
        
        since = datetime.now() - timedelta(days=days)
        commits = self.db.query(Commit).filter(
            Commit.committed_date >= since
        ).all()
        
        # Peak hours
        hours = {}
        for commit in commits:
            hour = commit.committed_date.hour
            hours[hour] = hours.get(hour, 0) + 1
        
        peak_hour = max(hours, key=hours.get) if hours else None
        
        # Day of week patterns
        days_of_week = {}
        for commit in commits:
            day = commit.committed_date.strftime('%A')
            days_of_week[day] = days_of_week.get(day, 0) + 1
        
        best_day = max(days_of_week, key=days_of_week.get) if days_of_week else None
        
        # Most edited files
        file_changes = {}
        for commit in commits:
            for file in commit.files:
                file_changes[file.file_path] = file_changes.get(file.file_path, 0) + 1
        
        hot_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'peak_hour': peak_hour,
            'best_day': best_day,
            'hot_files': [{'path': f[0], 'changes': f[1]} for f in hot_files],
            'hourly_distribution': hours,
            'daily_distribution': days_of_week
        }
    
    def get_repository_breakdown(self, days: int = 30) -> List[Dict]:
        """Get commits per repository"""
        from models import Repository, Commit
        
        since = datetime.now() - timedelta(days=days)
        
        results = self.db.query(
            Repository.name,
            func.count(Commit.id).label('commit_count'),
            func.sum(Commit.insertions).label('lines_added'),
            func.sum(Commit.deletions).label('lines_deleted')
        ).join(Commit).filter(
            Commit.committed_date >= since
        ).group_by(Repository.id).order_by(
            func.count(Commit.id).desc()
        ).all()
        
        return [
            {
                'repository': r[0],
                'commits': r[1],
                'lines_added': r[2] or 0,
                'lines_deleted': r[3] or 0
            }
            for r in results
        ]
    
    def _score_commit_messages(self, messages: List[str]) -> float:
        """Score commit messages (0-100)"""
        if not messages:
            return 0.0
        
        conventional_commits = 0
        good_length = 0
        
        for msg in messages:
            # Check conventional commit format
            if msg.startswith(('feat:', 'fix:', 'refactor:', 'docs:', 'test:', 'chore:')):
                conventional_commits += 1
            
            # Check length (7-72 chars recommended)
            if 7 <= len(msg) <= 72:
                good_length += 1
        
        score = (conventional_commits / len(messages)) * 50
        score += (good_length / len(messages)) * 50
        
        return min(100, score)
    
    def _calculate_time_spread(self, commits: List) -> float:
        """Calculate how spread out commits are across the day (0-100)"""
        if not commits:
            return 0.0
        
        hours = [c.committed_date.hour for c in commits]
        
        # More spread across day = higher score
        unique_hours = len(set(hours))
        max_hours = 24
        
        return (unique_hours / max_hours) * 100
    
    def _serialize_daily_stat(self, stat) -> Dict:
        """Serialize daily stat to dict"""
        return {
            'date': stat.date.isoformat(),
            'commit_count': stat.commit_count,
            'lines_added': stat.total_lines_added,
            'lines_deleted': stat.total_lines_deleted,
            'files_touched': stat.files_touched,
            'message_quality': stat.commit_convention_score,
            'productivity_score': self.get_productivity_score(stat.date)
        }
```

### 3. CLI Commands

```python
# src/cli/commands/report.py
import click
from datetime import datetime, timedelta, date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.chart import BarChart
from src.scraper.git_scraper import GitScraper
from src.analytics.analytics_engine import AnalyticsEngine

console = Console()

@click.group()
def report():
    """Reporting commands"""
    pass

@report.command()
@click.option('--date', default='today',
              help='Date (today, yesterday, YYYY-MM-DD)')
def daily(date: str):
    """Daily commit report"""
    from src.db import get_session
    
    session = get_session()
    analytics = AnalyticsEngine(session)
    
    # Parse date
    if date == 'today':
        target_date = datetime.now().date()
    elif date == 'yesterday':
        target_date = datetime.now().date() - timedelta(days=1)
    else:
        target_date = datetime.fromisoformat(date).date()
    
    # Get stats
    stats = analytics.get_daily_stats(target_date)
    score = analytics.get_productivity_score(target_date)
    patterns = analytics.detect_patterns(days=30)
    repos = analytics.get_repository_breakdown()
    
    # Display report
    console.print(f"\n[bold]📊 Daily Report - {target_date}[/bold]\n")
    
    # Summary
    console.print(f"Commits: {stats['commit_count']}")
    console.print(f"Lines Added: +{stats['lines_added']}")
    console.print(f"Lines Deleted: -{stats['lines_deleted']}")
    console.print(f"Files Touched: {stats['files_touched']}")
    console.print(f"Productivity Score: {score:.1f}/100\n")
    
    # Repos breakdown
    if repos:
        table = Table(title="Repository Breakdown")
        table.add_column("Repository", style="cyan")
        table.add_column("Commits", style="magenta")
        table.add_column("Lines Added", style="green")
        table.add_column("Lines Deleted", style="red")
        
        for repo in repos:
            table.add_row(
                repo['repository'],
                str(repo['commits']),
                str(repo['lines_added']),
                str(repo['lines_deleted'])
            )
        
        console.print(table)

@report.command()
@click.option('--weeks', default=4, help='Number of weeks')
def weekly(weeks: int):
    """Weekly productivity report"""
    from src.db import get_session
    
    session = get_session()
    analytics = AnalyticsEngine(session)
    
    today = datetime.now().date()
    
    for w in range(weeks):
        week_start = today - timedelta(days=today.weekday() + (7 * w))
        
        report_data = analytics.get_weekly_report(week_start)
        
        console.print(f"\n[bold]Week of {week_start}[/bold]")
        console.print(f"Commits: {report_data['total_commits']}")
        console.print(f"Active Days: {report_data['active_days']}/7")
        console.print(f"Average/Day: {report_data['avg_per_day']:.1f}")
        console.print(f"Lines: +{report_data['lines_added']} -{report_data['lines_deleted']}\n")

@report.command()
@click.option('--author', default=None, help='Filter by author')
def streaks(author: str):
    """Show commit streaks"""
    from src.db import get_session
    from models import Commit
    
    session = get_session()
    analytics = AnalyticsEngine(session)
    
    # Get unique authors if not specified
    if not author:
        authors = session.query(Commit.author).distinct().all()
        authors = [a[0] for a in authors]
    else:
        authors = [author]
    
    table = Table(title="Commit Streaks")
    table.add_column("Author", style="cyan")
    table.add_column("Current Streak", style="magenta")
    table.add_column("Status", style="green")
    
    for auth in authors:
        streak, is_current = analytics.get_current_streak(auth)
        status = "🔥 Active" if is_current else "❌ Broken"
        table.add_row(auth, str(streak), status)
    
    console.print(table)

@report.command()
@click.option('--days', default=30, help='Days to analyze')
def patterns(days: int):
    """Analyze commit patterns"""
    from src.db import get_session
    
    session = get_session()
    analytics = AnalyticsEngine(session)
    
    patterns_data = analytics.detect_patterns(days=days)
    
    console.print(f"\n[bold]📈 Commit Patterns (last {days} days)[/bold]\n")
    
    if patterns_data['peak_hour']:
        console.print(f"Peak Hour: {patterns_data['peak_hour']}:00 (UTC)")
    
    if patterns_data['best_day']:
        console.print(f"Best Day: {patterns_data['best_day']}")
    
    if patterns_data['hot_files']:
        console.print("\nMost Changed Files:")
        for file in patterns_data['hot_files']:
            console.print(f"  • {file['path']} ({file['changes']} changes)")
```

### 4. Background Service (Commit Scraper)

```python
# src/scheduler/background_service.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BackgroundService:
    def __init__(self, config_dir: Path = Path.home() / '.gitflow'):
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.scheduler = BackgroundScheduler()
    
    def start(self):
        """Start background service"""
        # Scrape repos every hour
        self.scheduler.add_job(
            self._scrape_all_repos,
            CronTrigger(minute=0),  # Every hour
            id='scrape_repos',
            name='Scrape Git Repositories'
        )
        
        # Calculate stats daily
        self.scheduler.add_job(
            self._calculate_daily_stats,
            CronTrigger(hour=0, minute=1),  # 12:01 AM
            id='daily_stats',
            name='Calculate Daily Statistics'
        )
        
        # Send daily digest
        self.scheduler.add_job(
            self._send_daily_digest,
            CronTrigger(hour=8, minute=0),  # 8 AM
            id='daily_digest',
            name='Send Daily Digest'
        )
        
        self.scheduler.start()
        logger.info("Background service started")
    
    def _scrape_all_repos(self):
        """Scrape all tracked repositories"""
        from src.db import get_session
        from src.scraper.git_scraper import GitScraper
        
        session = get_session()
        scraper = GitScraper(session)
        
        total = scraper.scan_all_repos()
        logger.info(f"Scraped {total} new commits")
    
    def _calculate_daily_stats(self):
        """Calculate daily statistics"""
        from src.db import get_session
        from src.analytics.analytics_engine import AnalyticsEngine
        from datetime import date
        
        session = get_session()
        analytics = AnalyticsEngine(session)
        
        yesterday = date.today() - timedelta(days=1)
        analytics.get_daily_stats(yesterday)
        logger.info(f"Calculated stats for {yesterday}")
    
    def _send_daily_digest(self):
        """Send daily digest notification"""
        from src.db import get_session
        from src.analytics.analytics_engine import AnalyticsEngine
        from datetime import date
        from plyer import notification
        
        session = get_session()
        analytics = AnalyticsEngine(session)
        
        today = date.today()
        stats = analytics.get_daily_stats(today)
        score = analytics.get_productivity_score(today)
        
        message = f"📊 {stats['commit_count']} commits, Score: {score:.0f}/100"
        
        notification.notify(
            title="GitFlow Daily Digest",
            message=message,
            timeout=10
        )
        logger.info("Daily digest sent")
```

### 5. CLI Entry Point

```python
# src/cli/main.py
import click
from pathlib import Path
from src.cli.commands.report import report
from src.scraper.git_scraper import GitScraper
from src.db import get_session
from rich.console import Console

console = Console()

@click.group()
def cli():
    """GitFlow - Git commit analytics and tracking"""
    pass

# Add command groups
cli.add_command(report)

@cli.command()
@click.argument('repo-path', type=click.Path(exists=True))
def add(repo_path: str):
    """Add repository to tracking"""
    session = get_session()
    scraper = GitScraper(session)
    
    if scraper.add_repository(Path(repo_path)):
        console.print(f"[green]✓ Repository added: {repo_path}[/green]")
    else:
        console.print(f"[red]✗ Failed to add repository[/red]")

@cli.command()
def init_service():
    """Initialize and start background service"""
    from src.scheduler.background_service import BackgroundService
    
    service = BackgroundService()
    service.start()
    
    console.print("[green]✓ Background service started[/green]")
    console.print("  • Scrapes repos hourly")
    console.print("  • Calculates daily stats at midnight")
    console.print("  • Sends daily digest at 8 AM")

if __name__ == '__main__':
    cli()
```

---

## Web Dashboard (Optional)

### FastAPI Backend

```python
# src/dashboard/api/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, date
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/dashboard")
def get_dashboard():
    """Get dashboard overview"""
    from src.db import get_session
    from src.analytics.analytics_engine import AnalyticsEngine
    
    session = get_session()
    analytics = AnalyticsEngine(session)
    
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    daily_stats = analytics.get_daily_stats(today)
    weekly_stats = analytics.get_weekly_report(week_start)
    score = analytics.get_productivity_score(today)
    repos = analytics.get_repository_breakdown()
    patterns = analytics.detect_patterns()
    
    return {
        'today': daily_stats,
        'this_week': weekly_stats,
        'productivity_score': score,
        'repositories': repos,
        'patterns': patterns
    }

@app.get("/api/history/{days}")
def get_history(days: int = 30):
    """Get historical data for charts"""
    from src.db import get_session
    from src.analytics.analytics_engine import AnalyticsEngine
    from models import DailyStat
    
    session = get_session()
    
    since = date.today() - timedelta(days=days)
    stats = session.query(DailyStat).filter(
        DailyStat.date >= since
    ).order_by(DailyStat.date).all()
    
    return {
        'data': [
            {
                'date': str(stat.date),
                'commits': stat.commit_count,
                'score': stat.commit_convention_score,
                'lines_added': stat.total_lines_added
            }
            for stat in stats
        ]
    }

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time updates"""
    await websocket.accept()
    
    while True:
        from src.db import get_session
        from src.analytics.analytics_engine import AnalyticsEngine
        from datetime import date
        import asyncio
        
        session = get_session()
        analytics = AnalyticsEngine(session)
        
        today = date.today()
        stats = analytics.get_daily_stats(today)
        score = analytics.get_productivity_score(today)
        
        await websocket.send_json({
            'timestamp': datetime.now().isoformat(),
            'commits_today': stats['commit_count'],
            'score': score
        })
        
        await asyncio.sleep(30)  # Update every 30 seconds
```

### React Dashboard

```jsx
// src/dashboard/frontend/src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  
  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);
  
  const fetchDashboard = async () => {
    const res = await axios.get('http://localhost:8000/api/dashboard');
    const histRes = await axios.get('http://localhost:8000/api/history/30');
    setStats(res.data);
    setHistory(histRes.data.data);
  };
  
  if (!stats) return <div>Loading...</div>;
  
  return (
    <div className="p-8 bg-gray-50">
      <h1 className="text-4xl font-bold mb-8">📊 GitFlow Dashboard</h1>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <Card label="Today's Commits" value={stats.today.commit_count} />
        <Card label="Productivity Score" value={`${stats.productivity_score.toFixed(0)}/100`} />
        <Card label="Lines Added" value={stats.today.lines_added} />
        <Card label="Weekly Commits" value={stats.this_week.total_commits} />
      </div>
      
      {/* Commits Over Time */}
      <div className="bg-white p-6 rounded-lg shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">Commits Trend (30 days)</h2>
        <LineChart width={600} height={300} data={history}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="commits" stroke="#3b82f6" />
        </LineChart>
      </div>
      
      {/* Productivity Score Trend */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Productivity Trend</h2>
        <LineChart width={600} height={300} data={history}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Line type="monotone" dataKey="score" stroke="#10b981" />
        </LineChart>
      </div>
    </div>
  );
}

function Card({ label, value }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="text-gray-600 text-sm">{label}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
}
```

---

## Build Steps for AI Agent

### Phase 1: Foundation (Days 1-2)
1. Create project structure
2. Set up SQLite database with schema
3. Implement `GitScraper` class
4. Test repository discovery and commit parsing
5. Implement database models (SQLAlchemy)

### Phase 2: Analytics (Days 3-4)
1. Implement `AnalyticsEngine` class
2. Create stat calculation methods
3. Implement productivity scoring
4. Add pattern detection
5. Create caching layer

### Phase 3: CLI Interface (Days 5-6)
1. Create Click command structure
2. Implement report commands
3. Add pretty output with Rich
4. Test all CLI commands
5. Add configuration management

### Phase 4: Background Service (Days 7-8)
1. Set up APScheduler
2. Implement scheduled scraping
3. Add stat calculation jobs
4. Create notification dispatch
5. Test automated workflows

### Phase 5: Web Dashboard (Days 9-10)
1. Create FastAPI application
2. Implement REST endpoints
3. Add WebSocket for real-time updates
4. Create React frontend
5. Add visualizations with Recharts

---

## Agent Prompt for Code Generation

```
You are building GitFlow, a comprehensive Git analytics and commit tracking tool.

CORE REQUIREMENTS:
1. Git repository scanning and commit extraction
2. SQLite database for storage with proper indexing
3. Daily/weekly/monthly analytics and reporting
4. Productivity scoring algorithm
5. Pattern detection (peak hours, hot files, etc.)
6. Commit streak tracking
7. Background service for automated scraping
8. CLI interface with Rich output
9. Optional web dashboard with real-time updates

IMPLEMENTATION APPROACH:
- Use GitPython for repository access
- Click for CLI framework
- SQLAlchemy for ORM
- APScheduler for background jobs
- FastAPI for optional dashboard
- React for frontend visualization

START WITH: Git scraper implementation
GOAL: User can add repos and see commits extracted to database

All code should include:
- Type hints (Python)
- Error handling for invalid repos
- Database transaction management
- Logging statements
- Proper indexing for query performance
```

---

## Usage Examples

```bash
# Add repository to tracking
gitflow add ~/projects/myapp

# View daily report
gitflow report daily --date today

# View weekly stats
gitflow report weekly --weeks 4

# Check commit streaks
gitflow report streaks

# Analyze patterns
gitflow report patterns --days 30

# Start background service
gitflow init-service

# Launch web dashboard
gitflow dashboard

# Export commits to CSV
gitflow export --format csv --output commits.csv
```

---

## Testing Checklist

- [ ] Git repository detection works
- [ ] Commits are correctly extracted and parsed
- [ ] Database persists across restarts
- [ ] Daily stats calculation is accurate
- [ ] Productivity score reflects work quality
- [ ] Pattern detection finds peak hours
- [ ] Streak tracking works correctly
- [ ] CLI commands provide clear output
- [ ] Background service runs on schedule
- [ ] Web dashboard updates in real-time
- [ ] Multiple repositories tracked simultaneously

