import click
from pathlib import Path
from datetime import datetime, timedelta
from src.gitflow.cli.commands.report import report
from src.gitflow.scraper.git_scraper import GitScraper
from src.gitflow.db import get_session
from src.gitflow.config import Config
from rich.console import Console

console = Console()


@click.group()
@click.version_option(version='1.0.0')
@click.option('--config', 'config_path', default=None, help='Path to config file', envvar='GITFLOW_CONFIG')
@click.pass_context
def cli(ctx, config_path):
    """GitFlow - Git commit analytics and tracking"""
    if config_path:
        Config.load(Path(config_path))
    else:
        Config.load()
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config_path


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

    scrape_interval = Config.get('gitflow.scrape_interval_hours', 1)
    stats_time = Config.get('scheduler.daily_stats_time', '00:01')
    digest_time = Config.get('scheduler.daily_digest_time', '08:00')

    console.print("[green]Background service started[/green]")
    console.print(f"  - Scrapes repos every {scrape_interval}h")
    console.print(f"  - Calculates daily stats at {stats_time}")
    console.print(f"  - Sends daily digest at {digest_time}")


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


@cli.command()
def config_show():
    """Show current configuration"""
    from rich.table import Table

    config_data = Config._config if Config._config else Config.load()

    table = Table(title="GitFlow Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    def flatten_dict(d, prefix=''):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                flatten_dict(v, key)
            else:
                table.add_row(key, str(v) if v is not None else '[dim]not set[/dim]')

    flatten_dict(config_data)
    console.print(table)


@cli.command()
@click.argument('key')
@click.argument('value')
def config_set(key: str, value: str):
    """Set a configuration value (e.g. gitflow.scrape_interval_hours 2)"""
    config_data = Config._config if Config._config else Config.load()

    keys = key.split('.')
    target = config_data
    for k in keys[:-1]:
        if k not in target:
            target[k] = {}
        target = target[k]

    try:
        if value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.lower() in ('none', 'null'):
                    value = None
    except (ValueError, AttributeError):
        pass

    target[keys[-1]] = value
    Config.save(config_data)
    console.print(f"[green]Set {key} = {value}[/green]")


@cli.command()
def config_reset():
    """Reset configuration to defaults"""
    Config.reset()
    console.print("[green]Configuration reset to defaults[/green]")


if __name__ == '__main__':
    cli()
