import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


@pytest.fixture
def temp_git_repo():
    repo_dir = tempfile.mkdtemp()
    subprocess.run(['git', 'init'], cwd=repo_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_dir, capture_output=True)

    test_file = Path(repo_dir) / 'test.txt'
    for i in range(5):
        test_file.write_text(f'content {i}\n')
        subprocess.run(['git', 'add', '.'], cwd=repo_dir, capture_output=True)
        day = (datetime.now() - timedelta(days=4 - i)).strftime('%Y-%m-%d')
        subprocess.run(
            ['git', 'commit', '-m', f'feat: commit {i} - testing'],
            cwd=repo_dir, capture_output=True,
            env={'GIT_AUTHOR_DATE': f'{day}T12:00:00',
                 'GIT_COMMITTER_DATE': f'{day}T12:00:00'}
        )

    yield Path(repo_dir)
    shutil.rmtree(repo_dir, ignore_errors=True)


@pytest.fixture
def temp_repo_no_commits():
    repo_dir = tempfile.mkdtemp()
    subprocess.run(['git', 'init'], cwd=repo_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@test.com'], cwd=repo_dir, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_dir, capture_output=True)

    yield Path(repo_dir)
    shutil.rmtree(repo_dir, ignore_errors=True)


@pytest.fixture
def db_session():
    from src.gitflow.db import get_session
    from src.gitflow.models import Base
    from sqlalchemy import create_engine

    tmp_db = Path(tempfile.mktemp(suffix='.db'))
    engine = create_engine(f'sqlite:///{tmp_db}', echo=False)
    Base.metadata.create_all(engine)

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()
    if tmp_db.exists():
        try:
            tmp_db.unlink()
        except PermissionError:
            pass


@pytest.fixture
def seeded_db_session(db_session):
    from src.gitflow.models import Repository, Commit, CommitFile

    repo = Repository(
        path='/tmp/test-repo',
        name='test-repo',
        remote_url='https://github.com/test/test-repo.git',
        default_branch='main'
    )
    db_session.add(repo)
    db_session.flush()

    recent_date = datetime.now() - timedelta(days=2)
    recent_date = recent_date.replace(hour=10, minute=0, second=0, microsecond=0)

    for i in range(3):
        commit_date = recent_date + timedelta(hours=i)
        commit = Commit(
            repo_id=repo.id,
            commit_hash=f'abc{i}def{i}ghi{i}jkl{i}mno{i}{i}',
            author='Test Author',
            author_email='author@test.com',
            message=f'feat: test commit {i}\n\nDetails here',
            message_summary=f'feat: test commit {i}',
            committed_date=commit_date,
            files_changed=2,
            insertions=10 + i * 5,
            deletions=2 + i,
            net_change=8 + i * 4,
            branch='main'
        )
        db_session.add(commit)
        db_session.flush()

        for j, fname in enumerate(['main.py', 'utils.py']):
            cf = CommitFile(
                commit_id=commit.id,
                file_path=f'src/{fname}',
                status='modified',
                insertions=5 + j,
                deletions=1 + j
            )
            db_session.add(cf)

    db_session.commit()

    yield db_session
