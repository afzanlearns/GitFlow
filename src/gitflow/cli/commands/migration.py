import click
from rich.console import Console
import subprocess
import sys
from pathlib import Path

console = Console()


@click.group()
def migration():
    """Database migration management (Alembic)"""
    pass


@migration.command()
@click.argument('name')
def create(name: str):
    """Create a new migration revision"""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'revision', '--autogenerate', '-m', name],
        capture_output=True, text=True, cwd=_get_project_root()
    )
    if result.returncode == 0:
        console.print(f"[green]{result.stdout.strip()}[/green]")
    else:
        console.print(f"[red]{result.stderr.strip()}[/red]")
        raise SystemExit(1)


@migration.command()
def upgrade():
    """Apply all pending migrations"""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'upgrade', 'head'],
        capture_output=True, text=True, cwd=_get_project_root()
    )
    if result.returncode == 0:
        console.print(f"[green]{result.stdout.strip()}[/green]")
    else:
        console.print(f"[red]{result.stderr.strip()}[/red]")
        raise SystemExit(1)


@migration.command()
def downgrade():
    """Revert last migration"""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'downgrade', '-1'],
        capture_output=True, text=True, cwd=_get_project_root()
    )
    if result.returncode == 0:
        console.print(f"[green]{result.stdout.strip()}[/green]")
    else:
        console.print(f"[red]{result.stderr.strip()}[/red]")
        raise SystemExit(1)


@migration.command()
def history():
    """Show migration history"""
    result = subprocess.run(
        [sys.executable, '-m', 'alembic', 'history'],
        capture_output=True, text=True, cwd=_get_project_root()
    )
    if result.returncode == 0:
        output = result.stdout.strip()
        if output:
            console.print(output)
        else:
            console.print("[yellow]No migrations have been applied[/yellow]")
    else:
        console.print(f"[red]{result.stderr.strip()}[/red]")
        raise SystemExit(1)


def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent.parent
