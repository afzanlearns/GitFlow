from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, and_, or_
import numpy as np


class AnalyticsEngine:
    def __init__(self, db_session):
        self.db = db_session

    def get_daily_stats(self, target_date: date) -> Dict:
        from src.gitflow.models import Commit, DailyStat
        from sqlalchemy import func

        cached = self.db.query(DailyStat).filter_by(date=target_date).first()
        if cached:
            return self._serialize_daily_stat(cached)

        commits = self.db.query(Commit).filter(
            func.date(Commit.committed_date) == target_date
        ).all()

        if not commits:
            return {
                'date': target_date.isoformat(),
                'commit_count': 0,
                'lines_added': 0,
                'lines_deleted': 0,
                'files_touched': 0,
                'message_quality': 0,
                'productivity_score': 0.0
            }

        commit_count = len(commits)
        total_added = sum(c.insertions for c in commits)
        total_deleted = sum(c.deletions for c in commits)
        repos_worked = len(set(c.repo_id for c in commits))
        files_touched = len(set(
            f.file_path for c in commits for f in c.files
        ))

        avg_msg_length = np.mean([len(c.message_summary or '') for c in commits])
        convention_score = self._score_commit_messages([c.message_summary or '' for c in commits])

        daily_stat = DailyStat(
            date=target_date,
            commit_count=commit_count,
            total_lines_added=total_added,
            total_lines_deleted=total_deleted,
            files_touched=files_touched,
            repos_worked_on=repos_worked,
            avg_commit_message_length=int(avg_msg_length),
            commit_convention_score=convention_score
        )

        self.db.add(daily_stat)
        self.db.commit()

        return self._serialize_daily_stat(daily_stat)

    def get_weekly_report(self, week_start: date) -> Dict:
        from src.gitflow.models import Commit, WeeklyStat

        week_end = week_start + timedelta(days=6)

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
            return {'week_start': week_start.isoformat(), 'total_commits': 0}

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

        weekly = WeeklyStat(
            week_start=week_start,
            week_end=week_end,
            commit_count=total_commits,
            total_lines_added=total_added,
            total_lines_deleted=total_deleted,
            avg_commits_per_day=avg_per_day,
            most_active_day=most_active_day.isoformat() if most_active_day else None
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
        from src.gitflow.models import Commit

        commits = self.db.query(Commit).filter(
            func.date(Commit.committed_date) == target_date
        ).all()

        if not commits:
            return 0.0

        commit_count = len(commits)
        freq_score = min(100, (commit_count / 5) * 100) * 0.3

        quality_score = self._score_commit_messages(
            [c.message_summary or '' for c in commits]
        ) * 0.3

        unique_files = len(set(
            f.file_path for c in commits for f in c.files
        ))
        diversity_score = min(100, (unique_files / 20) * 100) * 0.2

        time_spread = self._calculate_time_spread(commits)
        consistency_score = time_spread * 0.2

        total_score = freq_score + quality_score + diversity_score + consistency_score
        return min(100, total_score)

    def get_current_streak(self, author: str) -> Tuple[int, bool]:
        from src.gitflow.models import Commit

        today = datetime.now().date()
        current_streak = 0
        is_current = False

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
        from src.gitflow.models import Commit

        since = datetime.now() - timedelta(days=days)
        commits = self.db.query(Commit).filter(
            Commit.committed_date >= since
        ).all()

        hours = {}
        for commit in commits:
            hour = commit.committed_date.hour
            hours[hour] = hours.get(hour, 0) + 1

        peak_hour = max(hours, key=hours.get) if hours else None

        days_of_week = {}
        for commit in commits:
            day = commit.committed_date.strftime('%A')
            days_of_week[day] = days_of_week.get(day, 0) + 1

        best_day = max(days_of_week, key=days_of_week.get) if days_of_week else None

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
        from src.gitflow.models import Repository, Commit

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

    def get_monthly_report(self, year: int, month: int) -> Dict:
        from src.gitflow.models import Commit, MonthlyStat

        cached = self.db.query(MonthlyStat).filter_by(year=year, month=month).first()
        if cached:
            return {
                'year': cached.year,
                'month': cached.month,
                'commit_count': cached.commit_count,
                'lines_added': cached.total_lines_added,
                'lines_deleted': cached.total_lines_deleted,
                'avg_per_day': cached.avg_commits_per_day,
                'productivity_score': cached.productivity_score
            }

        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        commits = self.db.query(Commit).filter(
            and_(
                func.date(Commit.committed_date) >= first_day,
                func.date(Commit.committed_date) <= last_day
            )
        ).all()

        if not commits:
            return {'year': year, 'month': month, 'commit_count': 0}

        total_commits = len(commits)
        total_added = sum(c.insertions for c in commits)
        total_deleted = sum(c.deletions for c in commits)
        avg_per_day = total_commits / last_day.day

        score = self.get_productivity_score(first_day)

        monthly = MonthlyStat(
            year=year,
            month=month,
            commit_count=total_commits,
            total_lines_added=total_added,
            total_lines_deleted=total_deleted,
            avg_commits_per_day=avg_per_day,
            productivity_score=score
        )

        self.db.add(monthly)
        self.db.commit()

        return {
            'year': year,
            'month': month,
            'commit_count': total_commits,
            'lines_added': total_added,
            'lines_deleted': total_deleted,
            'avg_per_day': round(avg_per_day, 1),
            'productivity_score': round(score, 1)
        }

    def _score_commit_messages(self, messages: List[str]) -> float:
        if not messages:
            return 0.0

        conventional_commits = 0
        good_length = 0

        for msg in messages:
            if msg.startswith(('feat:', 'fix:', 'refactor:', 'docs:', 'test:', 'chore:', 'BREAKING:')):
                conventional_commits += 1

            if 7 <= len(msg) <= 72:
                good_length += 1

        score = (conventional_commits / len(messages)) * 50
        score += (good_length / len(messages)) * 50

        return min(100, score)

    def _calculate_time_spread(self, commits: List) -> float:
        if not commits:
            return 0.0

        hours = [c.committed_date.hour for c in commits]

        unique_hours = len(set(hours))

        return (unique_hours / 24) * 100

    def _serialize_daily_stat(self, stat) -> Dict:
        return {
            'date': stat.date.isoformat(),
            'commit_count': stat.commit_count,
            'lines_added': stat.total_lines_added,
            'lines_deleted': stat.total_lines_deleted,
            'files_touched': stat.files_touched,
            'message_quality': stat.commit_convention_score,
            'productivity_score': self.get_productivity_score(stat.date)
        }

    def _serialize_weekly_stat(self, stat) -> Dict:
        return {
            'week_start': stat.week_start.isoformat(),
            'week_end': stat.week_end.isoformat(),
            'total_commits': stat.commit_count,
            'lines_added': stat.total_lines_added,
            'lines_deleted': stat.total_lines_deleted,
            'avg_per_day': stat.avg_commits_per_day,
            'most_active_day': stat.most_active_day,
        }
