import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel

console = Console()


@click.command()
@click.pass_context
def setup(ctx):
    """Run the interactive setup wizard"""
    from src.gitflow.db import get_session
    from src.gitflow.scraper.git_scraper import GitScraper
    from src.gitflow.config import Config

    console.print(Panel.fit(
        "[bold cyan]GitFlow Setup Wizard[/bold cyan]\n"
        "Let's get you up and running with Git analytics.",
        border_style="cyan"
    ))

    config = Config.load()

    tracked_repos = []
    console.print("\n[bold]Step 1: Add Git Repositories[/bold]")
    console.print("Enter paths to Git repositories you want to track.")
    console.print("Type 'done' when finished.\n")

    while True:
        repo_path = Prompt.ask("  Repository path", default="" if tracked_repos else None)

        if not repo_path or repo_path.lower() == 'done':
            if not tracked_repos:
                console.print("[yellow]No repositories added. You can add them later with 'gitflow add <path>'[/yellow]")
            break

        path = Path(repo_path).expanduser().resolve()

        if not path.exists():
            console.print(f"[red]Path does not exist: {path}[/red]")
            continue

        session = get_session()
        scraper = GitScraper(session)

        if scraper.add_repository(path):
            tracked_repos.append(path)
            console.print(f"[green]  Added: {path}[/green]")
        else:
            console.print(f"[red]  Failed to add: {path} (not a valid git repository)[/red]")

        session.close()

    console.print(f"\n[bold]Step 2: Notification Settings[/bold]")

    want_email = Confirm.ask("  Want email digests?", default=False)
    if want_email:
        email = Prompt.ask("  Email address")
        config['notifications']['email_enabled'] = True
        config['notifications']['email_address'] = email

    slack_webhook = Prompt.ask("  Slack webhook URL (optional, press Enter to skip)", default="")
    if slack_webhook:
        config['notifications']['slack_webhook'] = slack_webhook

    console.print(f"\n[bold]Step 3: Analytics Settings[/bold]")

    threshold = Prompt.ask(
        "  Productivity threshold (0-100)",
        default=str(config['analytics']['productivity_threshold'])
    )
    try:
        config['analytics']['productivity_threshold'] = int(threshold)
    except ValueError:
        console.print("[yellow]Invalid value, keeping default[/yellow]")

    console.print(f"\n[bold]Step 4: UI Preferences[/bold]")

    theme = Prompt.ask("  Theme", choices=["dark", "light"], default=config['ui']['theme'])
    config['ui']['theme'] = theme

    console.print(f"\n[bold]Step 5: Background Service[/bold]")

    start_service = Confirm.ask("  Start background scraping service?", default=True)
    if start_service:
        from src.gitflow.scheduler.background_service import BackgroundService
        service = BackgroundService()
        service.start()
        console.print("[green]  Background service started[/green]")

    Config.save(config)

    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("\nTry these commands:")
    console.print("  [cyan]gitflow scan[/cyan]          - Scan repos for commits")
    console.print("  [cyan]gitflow report daily[/cyan]   - View today's stats")
    console.print("  [cyan]gitflow dashboard[/cyan]      - Launch web dashboard")
    console.print("  [cyan]gitflow config-show[/cyan]    - View current settings")
