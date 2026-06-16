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
        self.scheduler.add_job(
            self._scrape_all_repos,
            CronTrigger(minute=0),
            id='scrape_repos',
            name='Scrape Git Repositories'
        )

        self.scheduler.add_job(
            self._calculate_daily_stats,
            CronTrigger(hour=0, minute=1),
            id='daily_stats',
            name='Calculate Daily Statistics'
        )

        self.scheduler.add_job(
            self._send_daily_digest,
            CronTrigger(hour=8, minute=0),
            id='daily_digest',
            name='Send Daily Digest'
        )

        self.scheduler.start()
        logger.info("Background service started")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Background service stopped")

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

        logger.info(f"Daily digest: {message}")
        session.close()
