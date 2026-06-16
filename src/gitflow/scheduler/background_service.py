from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pathlib import Path
import logging
from datetime import datetime, timedelta, date

from gitflow.config import Config
from gitflow.models import ServiceStatus
from gitflow.notifications.notifier import NotificationService
from gitflow.db import get_session

logger = logging.getLogger(__name__)


class BackgroundService:
    def __init__(self, config_dir: Path = None):
        if config_dir is None:
            config_dir = Path.home() / '.gitflow'
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.scheduler = BackgroundScheduler()

    def start(self):
        scrape_interval = Config.get('gitflow.scrape_interval_hours', 1)
        stats_time = Config.get('scheduler.daily_stats_time', '00:01')
        digest_time = Config.get('scheduler.daily_digest_time', '08:00')

        stats_hour, stats_min = self._parse_time(stats_time)
        digest_hour, digest_min = self._parse_time(digest_time)

        self.scheduler.add_job(
            self._scrape_all_repos,
            CronTrigger(minute=0),
            id='scrape_repos',
            name='Scrape Git Repositories'
        )

        self.scheduler.add_job(
            self._calculate_daily_stats,
            CronTrigger(hour=stats_hour, minute=stats_min),
            id='daily_stats',
            name='Calculate Daily Statistics'
        )

        self.scheduler.add_job(
            self._send_daily_digest,
            CronTrigger(hour=digest_hour, minute=digest_min),
            id='daily_digest',
            name='Send Daily Digest'
        )

        self.scheduler.start()
        logger.info(f"Background service started (scrape every {scrape_interval}h, stats at {stats_time}, digest at {digest_time})")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Background service stopped")

    def _parse_time(self, time_str: str):
        try:
            parts = time_str.split(':')
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return 0, 1

    def _scrape_all_repos(self):
        from gitflow.scraper.git_scraper import GitScraper

        session = get_session()
        scraper = GitScraper(session)

        try:
            total = scraper.scan_all_repos()
            logger.info(f"Scraped {total} new commits")

            status = ServiceStatus(
                last_scrape=datetime.now(),
                last_scrape_status='success',
                commits_added=total,
            )
            session.add(status)
            session.commit()
        except Exception as e:
            logger.error(f"Scrape failed: {e}")
            status = ServiceStatus(
                last_scrape=datetime.now(),
                last_scrape_status='error',
                commits_added=0,
                error_message=str(e),
            )
            session.add(status)
            session.commit()
        finally:
            session.close()

    def _calculate_daily_stats(self):
        from gitflow.analytics.analytics_engine import AnalyticsEngine

        session = get_session()
        analytics = AnalyticsEngine(session)

        yesterday = datetime.now().date() - timedelta(days=1)
        stats = analytics.get_daily_stats(yesterday)
        logger.info(f"Calculated stats for {yesterday}: {stats.get('commit_count', 0)} commits")
        session.close()

    def _send_daily_digest(self):
        """Send daily digest notification"""
        from gitflow.analytics.analytics_engine import AnalyticsEngine

        session = get_session()
        try:
            analytics = AnalyticsEngine(session)

            today = date.today()
            stats = analytics.get_daily_stats(today)
            score = analytics.get_productivity_score(today)
            repos = analytics.get_repository_breakdown(days=1)

            # Actually send the notification
            NotificationService.send_daily_digest(stats, score, repos)

            # Log to ServiceStatus
            status = ServiceStatus(
                last_scrape=datetime.now(),
                last_scrape_status='success',
                commits_added=stats.get('commit_count', 0),
                error_message=None
            )
            session.add(status)
            session.commit()
        except Exception as e:
            logger.error(f"Failed to send daily digest: {e}")
        finally:
            session.close()
