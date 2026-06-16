import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from gitflow.dashboard.api.health import HealthChecker
from gitflow.db import get_session

console = Console()


@click.command()
def status():
    """Show system health status"""
    session = get_session()
    checker = HealthChecker(session)
    result = checker.full_health_check()
    session.close()

    table = Table(title="GitFlow System Health")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Detail", style="white")

    for check in result['checks']:
        status_str = "[green]PASS[/green]" if check['passed'] else "[red]FAIL[/red]"
        table.add_row(check['name'], status_str, check.get('detail', '') or '')

    overall = "[green]HEALTHY[/green]" if result['healthy'] else "[red]DEGRADED[/red]"
    console.print(Panel.fit(
        f"[bold]GitFlow Health Status:[/bold] {overall}\n"
        f"Timestamp: {result['timestamp']}",
        border_style="cyan"
    ))
    console.print(table)
