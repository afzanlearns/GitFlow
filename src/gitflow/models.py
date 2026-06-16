from sqlalchemy import Column, Integer, String, Boolean, Float, BigInteger, ForeignKey, Text, Date, DateTime, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Repository(Base):
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    remote_url = Column(String, nullable=True)
    default_branch = Column(String, default='main')
    tracked = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    commits = relationship('Commit', back_populates='repository')


class Commit(Base):
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    commit_hash = Column(String, unique=True, nullable=False)
    author = Column(String, nullable=False)
    author_email = Column(String, nullable=True)
    committer = Column(String, nullable=True)
    committer_email = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    message_summary = Column(String, nullable=True)
    committed_date = Column(DateTime, nullable=False)
    committed_unix = Column(BigInteger, nullable=True)
    files_changed = Column(Integer, default=0)
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    net_change = Column(Integer, default=0)
    is_merge = Column(Boolean, default=False)
    branch = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship('Repository', back_populates='commits')
    files = relationship('CommitFile', back_populates='commit')
    annotations = relationship('CommitAnnotation', back_populates='commit')
    tasks = relationship('TaskCommit', back_populates='commit')

    __table_args__ = (
        Index('idx_date', 'committed_date'),
        Index('idx_author', 'author'),
        Index('idx_repo', 'repo_id'),
    )


class CommitFile(Base):
    __tablename__ = 'commit_files'

    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False)
    file_path = Column(String, nullable=False)
    status = Column(String, nullable=True)
    insertions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)

    commit = relationship('Commit', back_populates='files')


class DailyStat(Base):
    __tablename__ = 'daily_stats'

    id = Column(Integer, primary_key=True)
    date = Column(Date, unique=True)
    commit_count = Column(Integer, default=0)
    total_lines_added = Column(Integer, default=0)
    total_lines_deleted = Column(Integer, default=0)
    files_touched = Column(Integer, default=0)
    repos_worked_on = Column(Integer, default=0)
    top_language = Column(String, nullable=True)
    avg_commit_message_length = Column(Integer, nullable=True)
    commit_convention_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class WeeklyStat(Base):
    __tablename__ = 'weekly_stats'

    id = Column(Integer, primary_key=True)
    week_start = Column(Date)
    week_end = Column(Date)
    commit_count = Column(Integer, default=0)
    total_lines_added = Column(Integer, default=0)
    total_lines_deleted = Column(Integer, default=0)
    avg_commits_per_day = Column(Float, default=0.0)
    most_active_day = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MonthlyStat(Base):
    __tablename__ = 'monthly_stats'

    id = Column(Integer, primary_key=True)
    year = Column(Integer)
    month = Column(Integer)
    commit_count = Column(Integer, default=0)
    total_lines_added = Column(Integer, default=0)
    total_lines_deleted = Column(Integer, default=0)
    avg_commits_per_day = Column(Float, default=0.0)
    productivity_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_year_month', 'year', 'month', unique=True),
    )


class CommitStreak(Base):
    __tablename__ = 'commit_streaks'

    id = Column(Integer, primary_key=True)
    author = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    days_count = Column(Integer, default=0)
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TaskCommit(Base):
    __tablename__ = 'tasks_commits'

    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False)
    task_id = Column(String, nullable=True)
    task_title = Column(String, nullable=True)
    project = Column(String, nullable=True)

    commit = relationship('Commit', back_populates='tasks')


class CommitAnnotation(Base):
    __tablename__ = 'commit_annotations'

    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False)
    label = Column(String, nullable=True)
    score = Column(Float, nullable=True)

    commit = relationship('Commit', back_populates='annotations')
