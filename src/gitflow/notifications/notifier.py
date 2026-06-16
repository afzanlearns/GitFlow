import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from src.gitflow.config import Config

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_slack(message: str, webhook_url: str = None) -> bool:
        """Send message to Slack via webhook"""
        if not webhook_url:
            webhook_url = Config.get('notifications.slack_webhook')
        
        if not webhook_url:
            logger.warning("Slack webhook not configured")
            return False
        
        try:
            payload = {
                'text': message,
                'mrkdwn': True  # Allow markdown formatting
            }
            response = requests.post(
                webhook_url,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("Slack notification sent")
                return True
            else:
                logger.error(f"Slack error: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False
    
    @staticmethod
    def send_email(recipient: str, subject: str, body_html: str) -> bool:
        """Send email via SMTP"""
        smtp_config = {
            'host': Config.get('notifications.smtp_host', 'smtp.gmail.com'),
            'port': Config.get('notifications.smtp_port', 587),
            'username': Config.get('notifications.smtp_username'),
            'password': Config.get('notifications.smtp_password')
        }
        
        if not smtp_config['username']:
            logger.warning("SMTP not configured")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = smtp_config['username']
            msg['To'] = recipient
            
            msg.attach(MIMEText(body_html, 'html'))
            
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipient}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    @staticmethod
    def send_daily_digest(daily_stats: dict, productivity_score: float, 
                         repo_breakdown: list) -> dict:
        """Send formatted daily digest"""
        results = {'slack': False, 'email': False}
        
        # Format Slack message
        slack_text = f"""📊 *GitFlow Daily Digest*
        
Commits: {daily_stats.get('commit_count', 0)}
Lines Added: +{daily_stats.get('lines_added', 0)}
Lines Deleted: -{daily_stats.get('lines_deleted', 0)}
Files Changed: {daily_stats.get('files_touched', 0)}
Productivity Score: {productivity_score:.0f}/100

Top Repos:"""
        
        for repo in repo_breakdown[:3]:
            slack_text += f"\n  • {repo['repository']}: {repo['commits']} commits"
        
        # Send to Slack
        results['slack'] = NotificationService.send_slack(slack_text)
        
        # Send email if configured
        email = Config.get('notifications.email_address')
        if email and Config.get('notifications.email_enabled'):
            html_body = f"""
            <h2>GitFlow Daily Digest</h2>
            <p><strong>Commits:</strong> {daily_stats.get('commit_count', 0)}</p>
            <p><strong>Score:</strong> {productivity_score:.0f}/100</p>
            <p><strong>Lines Added:</strong> +{daily_stats.get('lines_added', 0)}</p>
            <p><strong>Lines Deleted:</strong> -{daily_stats.get('lines_deleted', 0)}</p>
            """
            
            results['email'] = NotificationService.send_email(
                email,
                "GitFlow Daily Digest",
                html_body
            )
        return results
