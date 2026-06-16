from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pathlib import Path
import logging
from datetime import datetime, timedelta

from src.gitflow.config import Config

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
        from src.gitflow.db import get_session
        from src.gitflow.scraper.git_scraper import GitScraper

        session = get_session()
        scraper = GitScraper(session)

        total = scraper.scan_all_repos()
        logger.info(f"Scraped {total} new commits")
        session.close()

    def _calculate_daily_stats(self):
        from src.gitflow.db import get_session
        from src.gitflow.analytics.analytics_engine import AnalyticsEngine

        session = get_session()
        analytics = AnalyticsEngine(session)

        yesterday = datetime.now().date() - timedelta(days=1)
        stats = analytics.get_daily_stats(yesterday)
        logger.info(f"Calculated stats for {yesterday}: {stats.get('commit_count', 0)} commits")
        session.close()

    def _send_daily_digest(self):
        from src.gitflow.db import get_session
        from src.gitflow.analytics.analytics_engine import AnalyticsEngine

        session = get_session()
        analytics = AnalyticsEngine(session)

        notifications_enabled = Config.get('notifications.enabled', True)
        if not notifications_enabled:
            logger.info("Notifications disabled, skipping daily digest")
            session.close()
            return

        today = datetime.now().date()
        stats = analytics.get_daily_stats(today)
        score = analytics.get_productivity_score(today)

        message = f"{stats.get('commit_count', 0)} commits, Score: {score:.0f}/100"

        try:
            from plyer import notification
            notification.notify(
                title="GitFlow Daily Digest",
                message=message,
                timeout=10
            )
        except ImportError:
            logger.warning("Plyer not installed, skipping system notification")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

        slack_webhook = Config.get('notifications.slack_webhook')
        if slack_webhook:
            try:
                import requests
                requests.post(slack_webhook, json={'text': f'GitFlow Digest: {message}'}, timeout=5)
            except Exception as e:
                logger.error(f"Failed to send Slack notification: {e}")

        logger.info(f"Daily digest: {message}")
        session.close()
