import click
from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps
from git.exc import InvalidGitRepositoryError
from gitflow.cli.commands.report import report
from gitflow.cli.commands.setup import setup
from gitflow.cli.commands.migration import migration
from gitflow.cli.commands.status import status
from gitflow.scraper.git_scraper import GitScraper
from gitflow.db import get_session
from gitflow.config import Config
from rich.console import Console

console = Console()


def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except InvalidGitRepositoryError as e:
            console.print(f"[red]Invalid repository: {e}[/red]")
            raise SystemExit(1)
        except click.Abort:
            raise
        except click.ClickException:
            raise
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Unexpected error")
            raise SystemExit(1)
    return wrapper


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
cli.add_command(setup)
cli.add_command(migration)
cli.add_command(status)


@cli.command()
@click.argument('repo-path', type=click.Path(exists=True))
@handle_errors
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
@handle_errors
def scan(since: str):
    """Scan repositories for new commits"""
    from gitflow.models import Repository

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
@handle_errors
def history(days: int):
    """Show commit history"""
    from gitflow.models import Commit
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
@handle_errors
def init_service():
    """Initialize and start background service"""
    from gitflow.scheduler.background_service import BackgroundService

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
@handle_errors
def dashboard(port: int):
    """Launch web dashboard"""
    import uvicorn
    console.print(f"[green]Starting dashboard on http://localhost:{port}[/green]")
    # Use the correct import path for the FastAPI app. The package lives under the 'gitflow' top‑level package, not under a separate 'src' namespace.
    uvicorn.run('gitflow.dashboard.api.main:app', host='0.0.0.0', port=port, reload=False)


@cli.command()
@click.option('--format', 'fmt', default='csv', type=click.Choice(['csv', 'json', 'markdown']))
@click.option('--output', default='gitflow_export', help='Output file name (without extension)')
@click.option('--days', default=30, help='Days of history to export')
@handle_errors
def export(fmt: str, output: str, days: int):
    """Export commit data"""
    import csv
    import json
    from gitflow.models import Commit

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
    elif fmt == 'markdown':
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# GitFlow Export\n\n")
            f.write(f"**Period:** Last {days} days  \n")
            f.write(f"**Total commits:** {len(data)}  \n\n")
            f.write(f"## Commits\n\n")
            f.write(f"| Date | Author | Message | Files | +/- |\n")
            f.write(f"|------|--------|---------|-------|-----|\n")
            for c in data:
                f.write(f"| {c['date'][:10]} | {c['author']} | {c['message'][:50] or ''} | {c['files_changed']} | +{c['insertions']}/-{c['deletions']} |\n")

    console.print(f"[green]Exported {len(data)} commits to {filepath}[/green]")
    session.close()


@cli.command()
@handle_errors
def repos():
    """List tracked repositories"""
    from gitflow.models import Repository
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
@handle_errors
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
@handle_errors
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
@handle_errors
def config_reset():
    """Reset configuration to defaults"""
    Config.reset()
    console.print("[green]Configuration reset to defaults[/green]")


@cli.group()
def token():
    """Manage API authentication tokens"""
    pass


@token.command()
@handle_errors
def generate():
    """Generate a new API token"""
    from gitflow.dashboard.api.auth import generate_token
    token = generate_token()
    console.print(f"[green]New API token generated:[/green]")
    console.print(f"[bold cyan]{token}[/bold cyan]")
    console.print("\nUse this token in the Authorization header:")
    console.print("  Authorization: Bearer <token>")


@token.command()
@handle_errors
def show():
    """Show current API token"""
    from gitflow.dashboard.api.auth import get_token
    token = get_token()
    if token:
        console.print(f"[green]Current API token:[/green]")
        console.print(f"[bold cyan]{token}[/bold cyan]")
    else:
        console.print("[yellow]No API token set. Run 'gitflow token generate'[/yellow]")


@token.command()
@handle_errors
def revoke():
    """Revoke current API token"""
    from gitflow.dashboard.api.auth import revoke_token
    revoke_token()
    console.print("[green]API token revoked[/green]")


cli.add_command(token)


if __name__ == '__main__':
    cli()
