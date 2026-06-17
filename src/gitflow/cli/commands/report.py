import click
from datetime import datetime, timedelta, date
from pathlib import Path
from rich.console import Console
from rich.table import Table
from gitflow.scraper.git_scraper import GitScraper
from gitflow.analytics.analytics_engine import AnalyticsEngine

console = Console()


@click.group()
def report():
    """Reporting commands"""
    pass


@report.command()
@click.option('--date', default='today', help='Date (today, yesterday, YYYY-MM-DD)')
def daily(date: str):
    """Daily commit report"""
    from gitflow.db import get_session

    session = get_session()
    analytics = AnalyticsEngine(session)

    if date == 'today':
        target_date = datetime.now().date()
    elif date == 'yesterday':
        target_date = datetime.now().date() - timedelta(days=1)
    else:
        target_date = datetime.fromisoformat(date).date()

    stats = analytics.get_daily_stats(target_date)
    score = analytics.get_productivity_score(target_date)
    patterns = analytics.detect_patterns(days=30)
    repos = analytics.get_repository_breakdown(since_date=target_date)

    console.print(f"\n[bold]Daily Report - {target_date}[/bold]\n")

    console.print(f"Commits: {stats['commit_count']}")
    console.print(f"Lines Added: +{stats['lines_added']}")
    console.print(f"Lines Deleted: -{stats['lines_deleted']}")
    console.print(f"Files Touched: {stats['files_touched']}")
    console.print(f"Productivity Score: {score:.1f}/100\n")

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

    if patterns.get('peak_hour'):
        console.print(f"\nPeak Hour: {patterns['peak_hour']}:00 (UTC)")
    if patterns.get('best_day'):
        console.print(f"Best Day: {patterns['best_day']}")

    session.close()


@report.command()
@click.option('--weeks', default=4, help='Number of weeks')
def weekly(weeks: int):
    """Weekly productivity report"""
    from gitflow.db import get_session

    session = get_session()
    analytics = AnalyticsEngine(session)

    today = datetime.now().date()

    for w in range(weeks):
        week_start = today - timedelta(days=today.weekday() + (7 * w))

        report_data = analytics.get_weekly_report(week_start)

        console.print(f"\n[bold]Week of {week_start}[/bold]")
        console.print(f"Commits: {report_data.get('total_commits', 0)}")
        console.print(f"Active Days: {report_data.get('active_days', 0)}/7")
        console.print(f"Average/Day: {report_data.get('avg_per_day', 0):.1f}")
        console.print(f"Lines: +{report_data.get('lines_added', 0)} -{report_data.get('lines_deleted', 0)}\n")

    session.close()


@report.command()
@click.option('--author', default=None, help='Filter by author')
def streaks(author: str):
    """Show commit streaks"""
    from gitflow.db import get_session
    from gitflow.models import Commit

    session = get_session()
    analytics = AnalyticsEngine(session)

    if not author:
        authors = session.query(Commit.author).distinct().all()
        authors = [a[0] for a in authors if a[0]]
    else:
        authors = [author]

    if not authors:
        console.print("[yellow]No authors found in commit history[/yellow]")
        session.close()
        return

    table = Table(title="Commit Streaks")
    table.add_column("Author", style="cyan")
    table.add_column("Current Streak", style="magenta")
    table.add_column("Status", style="green")

    for auth in authors:
        streak, is_current = analytics.get_current_streak(auth)
        status = "Active" if is_current else "Broken"
        table.add_row(auth, str(streak), status)

    console.print(table)
    session.close()


@report.command()
@click.option('--days', default=30, help='Days to analyze')
def patterns(days: int):
    """Analyze commit patterns"""
    from gitflow.db import get_session

    session = get_session()
    analytics = AnalyticsEngine(session)

    patterns_data = analytics.detect_patterns(days=days)

    console.print(f"\n[bold]Commit Patterns (last {days} days)[/bold]\n")

    if patterns_data.get('peak_hour'):
        console.print(f"Peak Hour: {patterns_data['peak_hour']}:00 (UTC)")

    if patterns_data.get('best_day'):
        console.print(f"Best Day: {patterns_data['best_day']}")

    if patterns_data.get('hot_files'):
        console.print("\nMost Changed Files:")
        for file in patterns_data['hot_files']:
            console.print(f"  - {file['path']} ({file['changes']} changes)")

    session.close()


@report.command()
@click.option('--year', default=None, type=int, help='Year')
@click.option('--month', default=None, type=int, help='Month')
def monthly(year: int, month: int):
    """Monthly report"""
    from gitflow.db import get_session

    session = get_session()
    analytics = AnalyticsEngine(session)

    today = datetime.now()
    if not year:
        year = today.year
    if not month:
        month = today.month

    data = analytics.get_monthly_report(year, month)

    console.print(f"\n[bold]Monthly Report - {year}-{month:02d}[/bold]\n")
    console.print(f"Commits: {data.get('commit_count', 0)}")
    console.print(f"Lines Added: +{data.get('lines_added', 0)}")
    console.print(f"Lines Deleted: -{data.get('lines_deleted', 0)}")
    console.print(f"Average/Day: {data.get('avg_per_day', 0):.1f}")
    console.print(f"Productivity Score: {data.get('productivity_score', 0)}/100\n")

    session.close()
