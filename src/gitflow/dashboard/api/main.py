from fastapi import FastAPI, Request, WebSocket, Query, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, date
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
import asyncio
import logging
import time

from gitflow.dashboard.api.auth import verify_token
from gitflow.dashboard.api.limiter import limiter, rate_limit_exceeded_handler
from gitflow.dashboard.api.schemas import FilterParams, SearchParams, ExportParams
from gitflow.dashboard.api.health import HealthChecker
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors()
        }
    )


async def optional_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is not None:
        try:
            return verify_token(credentials.credentials)
        except Exception:
            pass
    return True


@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    from gitflow.db import get_session

    session = get_session()
    checker = HealthChecker(session)
    result = checker.full_health_check()
    session.close()

    status_code = 200 if result['healthy'] else 503
    from fastapi.responses import JSONResponse
    return JSONResponse(content=result, status_code=status_code)


@app.get("/health/live")
@limiter.limit("100/minute")
async def liveness_probe(request: Request):
    return {'status': 'alive'}


@app.get("/health/ready")
@limiter.limit("100/minute")
async def readiness_probe(request: Request):
    from gitflow.db import get_session

    session = get_session()
    checker = HealthChecker(session)
    db_check = checker.check_db_connection()
    session.close()

    if db_check['passed']:
        return {'status': 'ready', 'database': 'connected'}
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={'status': 'not ready', 'database': db_check['detail']},
        status_code=503
    )


@app.get("/api/dashboard")
@limiter.limit("10/minute")
async def get_dashboard(request: Request, auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.analytics.analytics_engine import AnalyticsEngine

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
@limiter.limit("10/minute")
async def get_history(request: Request, days: int = 30, auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import DailyStat

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
@limiter.limit("20/minute")
async def get_repos(request: Request, auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Repository

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
@limiter.limit("10/minute")
async def get_streaks(request: Request, auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Commit
    from gitflow.analytics.analytics_engine import AnalyticsEngine

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
@limiter.limit("30/minute")
async def search(request: Request, params: SearchParams = Depends(), auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Commit, CommitFile

    session = get_session()
    start_time = time.time()

    results = []

    if params.category == 'commits':
        query = session.query(Commit).filter(
            Commit.message_summary.ilike(f'%{params.q}%')
        ).order_by(Commit.committed_date.desc()).limit(params.limit).all()

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

    elif params.category == 'files':
        query = session.query(CommitFile).filter(
            CommitFile.file_path.ilike(f'%{params.q}%')
        ).limit(params.limit).all()

        file_set = {}
        for f in query:
            if f.file_path not in file_set:
                file_set[f.file_path] = 0
            file_set[f.file_path] += 1

        results = [
            {'type': 'file', 'path': path, 'changes': count}
            for path, count in sorted(file_set.items(), key=lambda x: x[1], reverse=True)[:params.limit]
        ]

    elif params.category == 'authors':
        query = session.query(Commit.author, Commit.author_email).filter(
            Commit.author.ilike(f'%{params.q}%')
        ).distinct().limit(params.limit).all()

        results = [
            {'type': 'author', 'name': a[0], 'email': a[1]}
            for a in query if a[0]
        ]

    elapsed = time.time() - start_time
    if elapsed > 0.1:
        logger.warning(f"Slow search query ({elapsed:.2f}s): q={params.q}, category={params.category}")

    session.close()

    return {'results': results, 'count': len(results), 'query': params.q, 'category': params.category}


@app.get("/api/filter")
@limiter.limit("30/minute")
async def filter_commits(request: Request, params: FilterParams = Depends(), auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Commit, Repository, CommitFile

    session = get_session()

    since = datetime.now() - timedelta(days=params.days)
    query = session.query(Commit).join(Repository)

    query = query.filter(Commit.committed_date >= since)

    if params.author:
        query = query.filter(Commit.author.ilike(f'%{params.author}%'))
    if params.repo:
        query = query.filter(Repository.name.ilike(f'%{params.repo}%'))
    if params.language:
        subquery = session.query(CommitFile.commit_id).filter(
            CommitFile.file_path.ilike(f'%.{params.language}')
        ).subquery()
        query = query.filter(Commit.id.in_(subquery))

    total = query.count()
    query = query.order_by(Commit.committed_date.desc())
    query = query.offset((params.page - 1) * params.per_page).limit(params.per_page)

    commits = query.all()

    session.close()

    return {
        'total': total,
        'page': params.page,
        'per_page': params.per_page,
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
@limiter.limit("20/minute")
async def get_authors(request: Request, auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Commit
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
@limiter.limit("20/minute")
async def get_hot_files(request: Request, days: int = Query(30, description='Days of history'), auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Commit, CommitFile
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
    ).group_by(CommitFile.file_path).order_by(
        func.count(CommitFile.id).desc()
    ).limit(10).all()

    session.close()

    return [{'path': f[0], 'changes': f[1]} for f in files]


@app.get("/api/commit-by-language")
@limiter.limit("20/minute")
async def get_commits_by_language(request: Request, days: int = Query(30, description='Days of history'), auth=Depends(optional_auth)):
    from gitflow.db import get_session
    from gitflow.models import Commit, CommitFile
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


@app.post("/api/export")
@limiter.limit("5/minute")
async def export(request: Request, params: ExportParams = Depends(), auth=Depends(optional_auth)):
    """Export commits with validated parameters"""
    from gitflow.db import get_session
    from gitflow.models import Commit
    from fastapi.responses import Response

    session = get_session()
    since = datetime.now() - timedelta(days=params.days)
    commits = session.query(Commit).filter(Commit.committed_date >= since).all()
    session.close()

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
        })

    if params.format == 'json':
        from fastapi.responses import JSONResponse
        return JSONResponse(content=data)
    elif params.format == 'csv':
        import io
        import csv
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        return Response(content=output.getvalue(), media_type="text/csv")
    elif params.format == 'markdown':
        output_str = f"# GitFlow Export\n\n**Period:** Last {params.days} days  \n**Total commits:** {len(data)}  \n\n"
        output_str += "| Date | Author | Message | Files | +/- |\n|------|--------|---------|-------|-----|\n"
        for c in data:
            output_str += f"| {c['date'][:10]} | {c['author']} | {c['message'][:50] or ''} | {c['files_changed']} | +{c['insertions']}/-{c['deletions']} |\n"
        return Response(content=output_str, media_type="text/markdown")
    return {"status": "success", "count": len(data)}


@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        from gitflow.db import get_session
        from gitflow.analytics.analytics_engine import AnalyticsEngine

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
