import pytest
from datetime import datetime, timedelta, date
from gitflow.analytics.analytics_engine import AnalyticsEngine


class TestAnalyticsEngine:

    def _get_seeded_date(self, seeded_db_session):
        from gitflow.models import Commit
        first = seeded_db_session.query(Commit).first()
        return first.committed_date.date()

    def test_get_daily_stats_empty_day(self, db_session):
        analytics = AnalyticsEngine(db_session)
        result = analytics.get_daily_stats(date(2024, 1, 1))
        assert result['commit_count'] == 0
        assert result['lines_added'] == 0
        assert result['lines_deleted'] == 0
        assert result['files_touched'] == 0

    def test_get_daily_stats_with_commits(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        target = self._get_seeded_date(seeded_db_session)
        result = analytics.get_daily_stats(target)
        assert result['commit_count'] == 3
        assert result['lines_added'] == 45
        assert result['lines_deleted'] == 9

    def test_get_daily_stats_caching(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        target = self._get_seeded_date(seeded_db_session)
        first = analytics.get_daily_stats(target)
        second = analytics.get_daily_stats(target)
        assert first['commit_count'] == second['commit_count']
        assert first['lines_added'] == second['lines_added']

    def test_get_productivity_score_calculation(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        target = self._get_seeded_date(seeded_db_session)
        score = analytics.get_productivity_score(target)
        assert 0 <= score <= 100

    def test_get_productivity_score_zero_commits(self, db_session):
        analytics = AnalyticsEngine(db_session)
        score = analytics.get_productivity_score(date(2024, 6, 15))
        assert score == 0.0

    def test_get_productivity_score_edge_cases(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        target = self._get_seeded_date(seeded_db_session)
        score = analytics.get_productivity_score(target)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

        score_future = analytics.get_productivity_score(date(2099, 1, 1))
        assert score_future == 0.0

    def test_detect_patterns_peak_hour(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        patterns = analytics.detect_patterns(days=30)
        assert patterns['peak_hour'] == 10

    def test_detect_patterns_hot_files(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        patterns = analytics.detect_patterns(days=30)
        assert len(patterns['hot_files']) > 0
        for f in patterns['hot_files']:
            assert 'path' in f
            assert 'changes' in f

    def test_get_current_streak_continuous(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        streak, is_current = analytics.get_current_streak('Test Author')
        assert isinstance(streak, int)
        assert isinstance(is_current, bool)

    def test_get_current_streak_unknown_author(self, db_session):
        analytics = AnalyticsEngine(db_session)
        streak, is_current = analytics.get_current_streak('Unknown Author')
        assert streak == 0
        assert is_current is False

    def test_get_repository_breakdown(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        breakdown = analytics.get_repository_breakdown(days=30)
        assert len(breakdown) == 1
        assert breakdown[0]['repository'] == 'test-repo'
        assert breakdown[0]['commits'] == 3

    def test_get_weekly_report(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        target = self._get_seeded_date(seeded_db_session)
        week_start = target - timedelta(days=target.weekday())
        result = analytics.get_weekly_report(week_start)
        assert result['total_commits'] == 3
        assert result['most_active_day'] == target.isoformat()

    def test_get_weekly_report_empty(self, db_session):
        analytics = AnalyticsEngine(db_session)
        result = analytics.get_weekly_report(date(2024, 6, 1))
        assert result['total_commits'] == 0

    def test_get_monthly_report(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        target = self._get_seeded_date(seeded_db_session)
        result = analytics.get_monthly_report(target.year, target.month)
        assert result['commit_count'] == 3
        assert result['year'] == target.year
        assert result['month'] == target.month

    def test_score_commit_messages(self, db_session):
        analytics = AnalyticsEngine(db_session)
        messages = ['feat: add login', 'fix: resolve crash', 'random message']
        score = analytics._score_commit_messages(messages)
        assert score > 0

    def test_score_commit_messages_empty(self, db_session):
        analytics = AnalyticsEngine(db_session)
        score = analytics._score_commit_messages([])
        assert score == 0.0

    def test_calculate_time_spread(self, seeded_db_session):
        analytics = AnalyticsEngine(seeded_db_session)
        from gitflow.models import Commit
        commits = seeded_db_session.query(Commit).all()
        spread = analytics._calculate_time_spread(commits)
        assert 0 <= spread <= 100
