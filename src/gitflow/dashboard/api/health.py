from datetime import datetime
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class HealthChecker:
    def __init__(self, db_session):
        self.db = db_session

    def check_db_connection(self) -> Dict[str, Any]:
        try:
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
            return {'name': 'Database Connection', 'passed': True, 'detail': 'Connected'}
        except Exception as e:
            logger.error(f"Health check - DB connection failed: {e}")
            return {'name': 'Database Connection', 'passed': False, 'detail': str(e)}

    def check_last_scrape(self) -> Dict[str, Any]:
        try:
            from src.gitflow.models import ServiceStatus

            latest = self.db.query(ServiceStatus).order_by(
                ServiceStatus.created_at.desc()
            ).first()

            if not latest:
                return {'name': 'Last Scrape', 'passed': True, 'detail': 'No scrapes yet (normal on first run)'}

            if latest.last_scrape_status == 'error':
                return {'name': 'Last Scrape', 'passed': False, 'detail': f"Last scrape failed: {latest.error_message}"}

            if latest.last_scrape:
                minutes_ago = (datetime.now() - latest.last_scrape).total_seconds() / 60
                if minutes_ago > 70:
                    return {'name': 'Last Scrape', 'passed': False, 'detail': f"No scrapes in {minutes_ago:.0f} minutes"}
                detail = f"Last scrape: {minutes_ago:.0f} min ago ({latest.commits_added} commits)"
                return {'name': 'Last Scrape', 'passed': True, 'detail': detail}

            return {'name': 'Last Scrape', 'passed': True, 'detail': 'No scrape timestamp recorded'}
        except Exception as e:
            logger.error(f"Health check - last scrape failed: {e}")
            return {'name': 'Last Scrape', 'passed': False, 'detail': str(e)}

    def full_health_check(self) -> Dict[str, Any]:
        checks = [
            self.check_db_connection(),
            self.check_last_scrape(),
        ]

        all_passed = all(c['passed'] for c in checks)

        return {
            'status': 'healthy' if all_passed else 'degraded',
            'healthy': all_passed,
            'timestamp': datetime.now().isoformat(),
            'checks': checks,
        }
