import click
from pathlib import Path
from src.gitflow.cli.commands.report import report
from src.gitflow.scraper.git_scraper import GitScraper
from src.gitflow.db import get_session
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """GitFlow - Git commit analytics and tracking"""


cli.add_command(report)


@cli.command()
@click.argument('repo-path', type=click.Path(exists=True))
def add(repo_path: str):
    """Add repository to tracking"""
    session = get_session()
    scraper = GitScraper(session)

    if scraper.add_repository(Path(repo_path)):
        console.print(f"[green]Repository added: {repo_path}[/green]")
    else:
        console.print(f"[red]Failed to add repository[/red]")

    session.close()


@cli.command()
@click.option('--since', default='1day', help='Since when (1day, 7days, 30days, or YYYY-MM-DD)')
def scan(since: str):
    """Scan repositories for new commits"""
    from datetime import timedelta, datetime
    from src.gitflow.models import Repository

    session = get_session()
    scraper = GitScraper(session)

    repos = session.query(Repository).filter_by(tracked=True).all()

    if not repos:
        console.print("[yellow]No repositories tracked. Use 'gitflow add <path>' first.[/yellow]")
        session.close()
        return

    if since == '1day':
        since_date = datetime.now() - timedelta(days=1)
    elif since == '7days':
        since_date = datetime.now() - timedelta(days=7)
    elif since == '30days':
        since_date = datetime.now() - timedelta(days=30)
    else:
        try:
            since_date = datetime.strptime(since, '%Y-%m-%d')
        except ValueError:
            console.print("[red]Invalid date format. Use YYYY-MM-DD.[/red]")
            session.close()
            return

    total = 0
    for repo in repos:
        repo_path = Path(repo.path)
        if repo_path.exists():
            count = scraper.scan_commits_since(repo_path, since_date)
            total += count
            console.print(f"  {repo.name}: {count} new commits")
        else:
            console.print(f"[red]Repository path not found: {repo.path}[/red]")

    console.print(f"\n[green]Total: {total} new commits[/green]")
    session.close()


@cli.command()
@click.option('--days', default=30, help='Number of days for history')
def history(days: int):
    """Show commit history"""
    from src.gitflow.models import Commit
    from rich.table import Table

    session = get_session()
    since = datetime.now() - timedelta(days=days)

    commits = session.query(Commit).filter(
        Commit.committed_date >= since
    ).order_by(Commit.committed_date.desc()).limit(20).all()

    if not commits:
        console.print("[yellow]No commits found in this period[/yellow]")
        session.close()
        return

    table = Table(title=f"Recent Commits (last {days} days)")
    table.add_column("Date", style="cyan")
    table.add_column("Author", style="magenta")
    table.add_column("Repo", style="green")
    table.add_column("Message", style="white")

    for c in commits:
        table.add_row(
            c.committed_date.strftime('%Y-%m-%d %H:%M'),
            c.author,
            c.repository.name if c.repository else '?',
            c.message_summary[:60] if c.message_summary else ''
        )

    console.print(table)
    session.close()


@cli.command()
def init_service():
    """Initialize and start background service"""
    from src.gitflow.scheduler.background_service import BackgroundService

    service = BackgroundService()
    service.start()

    console.print("[green]Background service started[/green]")
    console.print("  - Scrapes repos hourly")
    console.print("  - Calculates daily stats at midnight")
    console.print("  - Sends daily digest at 8 AM")


@cli.command()
@click.option('--port', default=8000, help='Port to serve on')
def dashboard(port: int):
    """Launch web dashboard"""
    import uvicorn
    console.print(f"[green]Starting dashboard on http://localhost:{port}[/green]")
    uvicorn.run('src.gitflow.dashboard.api.main:app', host='0.0.0.0', port=port, reload=False)


@cli.command()
@click.option('--format', 'fmt', default='csv', type=click.Choice(['csv', 'json']))
@click.option('--output', default='gitflow_export', help='Output file name (without extension)')
@click.option('--days', default=30, help='Days of history to export')
def export(fmt: str, output: str, days: int):
    """Export commit data"""
    import csv
    import json
    from src.gitflow.models import Commit

    session = get_session()
    since = datetime.now() - timedelta(days=days)

    commits = session.query(Commit).filter(
        Commit.committed_date >= since
    ).all()

    if not commits:
        console.print("[yellow]No commits to export[/yellow]")
        session.close()
        return

    data = []
    for c in commits:
        data.append({
            'commit_hash': c.commit_hash,
            'author': c.author,
            'author_email': c.author_email,
            'date': c.committed_date.isoformat(),
            'message': c.message_summary,
            'files_changed': c.files_changed,
            'insertions': c.insertions,
            'deletions': c.deletions,
            'branch': c.branch,
            'repo': c.repository.name if c.repository else '',
        })

    filepath = Path.cwd() / f"{output}.{fmt}"

    if fmt == 'csv':
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    elif fmt == 'json':
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    console.print(f"[green]Exported {len(data)} commits to {filepath}[/green]")
    session.close()


@cli.command()
def repos():
    """List tracked repositories"""
    from src.gitflow.models import Repository
    from rich.table import Table

    session = get_session()
    repos = session.query(Repository).filter_by(tracked=True).all()

    if not repos:
        console.print("[yellow]No repositories tracked[/yellow]")
        session.close()
        return

    table = Table(title="Tracked Repositories")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Branch", style="magenta")
    table.add_column("Remote", style="blue")

    for repo in repos:
        table.add_row(
            repo.name,
            repo.path,
            repo.default_branch,
            repo.remote_url or 'N/A'
        )

    console.print(table)
    session.close()


if __name__ == '__main__':
    cli()
