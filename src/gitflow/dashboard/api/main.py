from fastapi import FastAPI, WebSocket, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, date
import asyncio
import logging
import time

from src.gitflow.dashboard.api.auth import verify_token

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def optional_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is not None:
        try:
            return verify_token(credentials.credentials)
        except Exception:
            pass
    return True


@app.get("/api/dashboard")
def get_dashboard(auth=Depends(optional_auth)):
    from src.gitflow.db import get_session
    from src.gitflow.analytics.analytics_engine import AnalyticsEngine

    session = get_session()
    analytics = AnalyticsEngine(session)

    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    daily_stats = analytics.get_daily_stats(today)
    weekly_stats = analytics.get_weekly_report(week_start)
    score = analytics.get_productivity_score(today)
    repos = analytics.get_repository_breakdown()
    patterns = analytics.detect_patterns()

    session.close()

    return {
        'today': daily_stats,
        'this_week': weekly_stats,
        'productivity_score': score,
        'repositories': repos,
        'patterns': patterns
    }


@app.get("/api/history/{days}")
def get_history(days: int = 30, auth=Depends(optional_auth)):
    from src.gitflow.db import get_session
    from src.gitflow.models import DailyStat

    session = get_session()

    since = date.today() - timedelta(days=days)
    stats = session.query(DailyStat).filter(
        DailyStat.date >= since
    ).order_by(DailyStat.date).all()

    session.close()

    return {
        'data': [
            {
                'date': str(stat.date),
                'commits': stat.commit_count,
                'score': stat.commit_convention_score,
                'lines_added': stat.total_lines_added
            }
            for stat in stats
        ]
    }


@app.get("/api/repos")
def get_repos(auth=Depends(optional_auth)):
    from src.gitflow.db import get_session
    from src.gitflow.models import Repository

    session = get_session()
    repos = session.query(Repository).filter_by(tracked=True).all()
    session.close()

    return [
        {
            'id': r.id,
            'name': r.name,
            'path': r.path,
            'branch': r.default_branch,
            'remote_url': r.remote_url
        }
        for r in repos
    ]


@app.get("/api/streaks")
def get_streaks(auth=Depends(optional_auth)):
    from src.gitflow.db import get_session
    from src.gitflow.models import Commit
    from src.gitflow.analytics.analytics_engine import AnalyticsEngine

    session = get_session()
    analytics = AnalyticsEngine(session)

    authors = session.query(Commit.author).distinct().all()
    authors = [a[0] for a in authors if a[0]]

    results = []
    for author in authors:
        streak, is_current = analytics.get_current_streak(author)
        results.append({
            'author': author,
            'streak': streak,
            'is_current': is_current
        })

    session.close()
    return {'streaks': results}


@app.get("/api/search")
def search(
    q: str = Query('', description='Search query'),
    category: str = Query('commits', description='Search category: commits, files, authors'),
    limit: int = Query(20, description='Max results'),
    auth=Depends(optional_auth)
):
    from src.gitflow.db import get_session
    from src.gitflow.models import Commit, CommitFile

    session = get_session()
    start_time = time.time()

    results = []

    if category == 'commits':
        query = session.query(Commit).filter(
            Commit.message_summary.ilike(f'%{q}%')
        ).order_by(Commit.committed_date.desc()).limit(limit).all()

        results = [
            {
                'type': 'commit',
                'hash': c.commit_hash[:8],
                'author': c.author,
                'message': c.message_summary,
                'date': c.committed_date.isoformat(),
                'repo': c.repository.name if c.repository else '',
            }
            for c in query
        ]

    elif category == 'files':
        query = session.query(CommitFile).filter(
            CommitFile.file_path.ilike(f'%{q}%')
        ).limit(limit).all()

        file_set = {}
        for f in query:
            if f.file_path not in file_set:
                file_set[f.file_path] = 0
            file_set[f.file_path] += 1

        results = [
            {'type': 'file', 'path': path, 'changes': count}
            for path, count in sorted(file_set.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]

    elif category == 'authors':
        query = session.query(Commit.author, Commit.author_email).filter(
            Commit.author.ilike(f'%{q}%')
        ).distinct().limit(limit).all()

        results = [
            {'type': 'author', 'name': a[0], 'email': a[1]}
            for a in query if a[0]
        ]

    elapsed = time.time() - start_time
    if elapsed > 0.1:
        logger.warning(f"Slow search query ({elapsed:.2f}s): q={q}, category={category}")

    session.close()

    return {'results': results, 'count': len(results), 'query': q, 'category': category}


@app.get("/api/filter")
def filter_commits(
    author: str = Query(None, description='Filter by author'),
    repo: str = Query(None, description='Filter by repository name'),
    days: int = Query(30, description='Days of history'),
    language: str = Query(None, description='Filter by file language extension'),
    page: int = Query(1, description='Page number'),
    per_page: int = Query(50, description='Results per page'),
    auth=Depends(optional_auth)
):
    from src.gitflow.db import get_session
    from src.gitflow.models import Commit, Repository, CommitFile

    session = get_session()

    since = datetime.now() - timedelta(days=days)
    query = session.query(Commit).join(Repository)

    query = query.filter(Commit.committed_date >= since)

    if author:
        query = query.filter(Commit.author.ilike(f'%{author}%'))
    if repo:
        query = query.filter(Repository.name.ilike(f'%{repo}%'))
    if language:
        subquery = session.query(CommitFile.commit_id).filter(
            CommitFile.file_path.ilike(f'%.{language}')
        ).subquery()
        query = query.filter(Commit.id.in_(subquery))

    total = query.count()
    query = query.order_by(Commit.committed_date.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    commits = query.all()

    session.close()

    return {
        'total': total,
        'page': page,
        'per_page': per_page,
        'results': [
            {
                'hash': c.commit_hash[:8],
                'author': c.author,
                'message': c.message_summary,
                'date': c.committed_date.isoformat(),
                'files_changed': c.files_changed,
                'insertions': c.insertions,
                'deletions': c.deletions,
                'repo': c.repository.name if c.repository else '',
                'branch': c.branch,
            }
            for c in commits
        ]
    }


@app.get("/api/authors")
def get_authors(auth=Depends(optional_auth)):
    from src.gitflow.db import get_session
    from src.gitflow.models import Commit
    from sqlalchemy import func

    session = get_session()

    results = session.query(
        Commit.author,
        func.count(Commit.id).label('commit_count')
    ).filter(
        Commit.author.isnot(None)
    ).group_by(Commit.author).order_by(
        func.count(Commit.id).desc()
    ).all()

    session.close()

    return [
        {'name': r[0], 'commits': r[1]}
        for r in results
    ]


@app.get("/api/hot-files")
def get_hot_files(
    days: int = Query(30, description='Days of history'),
    auth=Depends(optional_auth)
):
    from src.gitflow.db import get_session
    from src.gitflow.models import Commit, CommitFile

    session = get_session()

    since = datetime.now() - timedelta(days=days)

    commit_ids = session.query(Commit.id).filter(
        Commit.committed_date >= since
    ).subquery()

    files = session.query(
        CommitFile.file_path,
        func.count(CommitFile.id).label('changes')
    ).filter(
        CommitFile.commit_id.in_(commit_ids)
    ).group_by(CommitFile.file_path).order_by(
        func.count(CommitFile.id).desc()
    ).limit(10).all()

    session.close()

    return [{'path': f[0], 'changes': f[1]} for f in files]


@app.get("/api/commit-by-language")
def get_commits_by_language(
    days: int = Query(30, description='Days of history'),
    auth=Depends(optional_auth)
):
    from src.gitflow.db import get_session
    from src.gitflow.models import Commit, CommitFile
    from sqlalchemy import func

    session = get_session()

    since = datetime.now() - timedelta(days=days)

    commit_ids = session.query(Commit.id).filter(
        Commit.committed_date >= since
    ).subquery()

    files = session.query(
        CommitFile.file_path,
        func.count(CommitFile.id).label('changes')
    ).filter(
        CommitFile.commit_id.in_(commit_ids)
    ).group_by(CommitFile.file_path).all()

    language_map = {}
    for f in files:
        ext = f[0].split('.')[-1] if '.' in f[0] else 'unknown'
        language_map[ext] = language_map.get(ext, 0) + f[1]

    session.close()

    return [
        {'language': lang, 'commits': count}
        for lang, count in sorted(language_map.items(), key=lambda x: x[1], reverse=True)
    ]


@app.get("/api/health")
def health():
    return {'status': 'ok', 'timestamp': datetime.now().isoformat()}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        from src.gitflow.db import get_session
        from src.gitflow.analytics.analytics_engine import AnalyticsEngine

        session = get_session()
        analytics = AnalyticsEngine(session)

        today = date.today()
        stats = analytics.get_daily_stats(today)
        score = analytics.get_productivity_score(today)

        session.close()

        await websocket.send_json({
            'timestamp': datetime.now().isoformat(),
            'commits_today': stats['commit_count'],
            'score': score
        })

        await asyncio.sleep(30)
