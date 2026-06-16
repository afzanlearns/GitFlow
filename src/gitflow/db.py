from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SASession
from functools import lru_cache

from src.gitflow.models import Base
from src.gitflow.config import Config


def get_engine(db_path: Path = None):
    if db_path is None:
        config_path = Config.get('gitflow.database_path', str(Path.home() / '.gitflow' / 'gitflow.db'))
        db_path = Path(config_path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


@lru_cache(maxsize=None)
def _get_cached_engine(db_path_str: str):
    return get_engine(Path(db_path_str))


def get_session(db_path: Path = None) -> SASession:
    if db_path is None:
        config_path = Config.get('gitflow.database_path', str(Path.home() / '.gitflow' / 'gitflow.db'))
        db_path = Path(config_path).expanduser()
    engine = _get_cached_engine(str(db_path))
    Session = sessionmaker(bind=engine)
    return Session()


def init_migrations():
    """Initialize database migrations if not already done"""
    import os
    import subprocess
    import sys
    migration_dir = Path(__file__).parent.parent.parent / 'alembic' / 'versions'
    if not list(migration_dir.glob('*.py')):
        # First run - create initial migration
        subprocess.run([sys.executable, '-m', 'alembic', 'revision', '--autogenerate', '-m', 'initial schema'], cwd=Path(__file__).parent.parent.parent)
        subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], cwd=Path(__file__).parent.parent.parent)

