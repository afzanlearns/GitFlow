from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SASession
from functools import lru_cache
import os

from src.gitflow.models import Base

DEFAULT_DB_PATH = Path.home() / '.gitflow' / 'gitflow.db'


def get_engine(db_path: Path = None):
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f'sqlite:///{db_path}', echo=False)
    Base.metadata.create_all(engine)
    return engine


@lru_cache(maxsize=None)
def _get_cached_engine(db_path_str: str):
    return get_engine(Path(db_path_str))


def get_session(db_path: Path = None) -> SASession:
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    engine = _get_cached_engine(str(db_path))
    Session = sessionmaker(bind=engine)
    return Session()
