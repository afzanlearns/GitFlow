from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta, date
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/dashboard")
def get_dashboard():
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
def get_history(days: int = 30):
    from src.gitflow.db import get_session
    from src.gitflow.analytics.analytics_engine import AnalyticsEngine
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
def get_repos():
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
def get_streaks():
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
