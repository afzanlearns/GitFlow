# GitFlow

**Git commit analytics and tracking tool** — Scans Git repositories, extracts commit data, calculates productivity metrics, detects patterns, and provides rich visualizations via CLI and web dashboard.

---

## Features

- **Repository Scanning** — Automatically discovers and tracks Git repositories, fetches commits across all branches
- **Commit Analytics** — Daily, weekly, and monthly statistics with caching for performance
- **Productivity Scoring** — Calculates a 0–100 score based on commit frequency, message quality, file diversity, and time consistency
- **Pattern Detection** — Identifies peak coding hours, most active days, and hot files
- **Commit Streaks** — Tracks consecutive commit days per author
- **CLI Interface** — Rich terminal output with tables, colors, and formatted reports
- **Background Service** — Automated hourly scraping, daily stat calculation, and desktop notifications
- **Web Dashboard** — Real-time charts and metrics via FastAPI + React (optional)

---

## Architecture

```
GitFlow
├── Core CLI (Python Click)
│   ├── Commit scraper (watches git repos)
│   ├── Daily/weekly/monthly reports
│   ├── Commit statistics & streaks
│   └── Scheduled scraping (background)
│
├── Data Processing
│   ├── Git repository walker
│   ├── Commit parser & diff analyzer
│   ├── Analytics engine
│   └── Pattern & anomaly detection
│
├── Database Layer (SQLite via SQLAlchemy)
│   ├── Repositories, Commits, Files
│   ├── Daily/Weekly/Monthly stats (cached)
│   ├── Commit streaks
│   └── Annotations & task links
│
├── Background Service (APScheduler)
│   ├── Hourly commit scraping
│   ├── Midnight stat calculation
│   └── Daily digest notifications
│
└── Web Dashboard (Optional)
    ├── FastAPI REST + WebSocket API
    ├── React frontend (Recharts)
    └── Real-time dashboard updates
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Git (available on PATH)
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/afzanlearns/GitFlow.git
cd GitFlow

# Install with pip (editable mode recommended)
pip install -e .

# Or install with all extras (dashboard + notifications)
pip install -e ".[all]"

# Install dependencies directly
pip install -r requirements.txt
```

### Basic Usage

```bash
# Add a repository to track
gitflow add ~/projects/myapp

# Scan for commits (all tracked repos, last 24 hours)
gitflow scan

# View today's report
gitflow report daily

# View weekly report (last 4 weeks)
gitflow report weekly --weeks 4

# Check commit streaks
gitflow report streaks

# Analyze commit patterns (last 30 days)
gitflow report patterns --days 30

# Export commits to CSV
gitflow export --format csv --output commits

# List tracked repositories
gitflow repos
```

---

## CLI Reference

### Global Options

| Flag | Description |
|------|-------------|
| `--help` | Show help message |
| `--version` | Show version |

### Commands

#### `add <repo-path>`

Add a Git repository to tracking.

```bash
gitflow add /path/to/repo
gitflow add C:\Users\me\projects\myapp
```

Validates the path is a valid Git repository and fetches remote metadata. Stores the path, name, default branch, and remote URL in the database.

#### `scan`

Scan all tracked repositories for new commits.

```bash
# Last 24 hours (default)
gitflow scan

# Last 7 days
gitflow scan --since 7days

# Last 30 days
gitflow scan --since 30days

# Custom date range
gitflow scan --since 2024-01-01
```

Iterates all branches, parses commits since the specified date, and inserts new ones into the database. Tracks files changed, insertions/deletions, merge status, and branch info.

#### `report daily`

Show a detailed daily report.

```bash
gitflow report daily
gitflow report daily --date yesterday
gitflow report daily --date 2024-01-15
```

Displays:
- Total commits, lines added/deleted, files touched
- Productivity score (0–100)
- Per-repository breakdown table
- Peak coding hour and best day of week

#### `report weekly`

Show weekly productivity summaries.

```bash
gitflow report weekly
gitflow report weekly --weeks 8
```

Displays per-week: commit count, active days (out of 7), average commits per day, lines added/deleted.

#### `report monthly`

Show monthly report for a specific month.

```bash
gitflow report monthly
gitflow report monthly --year 2024 --month 3
```

#### `report streaks`

Show current commit streaks per author.

```bash
gitflow report streaks
gitflow report streaks --author "Jane Doe"
```

#### `report patterns`

Analyze commit patterns over a period.

```bash
gitflow report patterns
gitflow report patterns --days 90
```

Shows peak coding hour, most active day of week, and top 5 most-changed files.

#### `history`

Show recent commit history.

```bash
gitflow history
gitflow history --days 7
```

#### `export`

Export commit data to CSV or JSON.

```bash
gitflow export --format csv --output my_commits
gitflow export --format json --output my_commits --days 90
```

#### `init-service`

Start the background scheduler service.

```bash
gitflow init-service
```

Launches APScheduler with three jobs:
- **Hourly**: scrapes all tracked repos for new commits
- **Midnight (12:01 AM)**: calculates and caches daily statistics
- **8:00 AM**: sends desktop notification with yesterday's digest

Run this in a terminal or set up as a system service/startup task.

#### `dashboard`

Launch the web dashboard.

```bash
gitflow dashboard
gitflow dashboard --port 3000
```

Starts the FastAPI server at `http://localhost:8000`. Open in browser to view the dashboard.

#### `repos`

List all tracked repositories with their paths, branches, and remote URLs.

```bash
gitflow repos
```

---

## Web Dashboard

### Backend (FastAPI)

The dashboard API provides REST endpoints and a WebSocket for real-time updates.

**API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `GET /api/dashboard` | Overview with today's stats, weekly report, score, repos, patterns |
| `GET /api/history/{days}` | Historical daily stats for charting |
| `GET /api/repos` | List tracked repositories |
| `GET /api/streaks` | Commit streaks per author |
| `GET /api/health` | Health check |
| `WS /ws/live` | Real-time updates every 30 seconds |

```bash
# Start the dashboard API
gitflow dashboard

# Or directly with uvicorn
uvicorn src.gitflow.dashboard.api.main:app --reload --port 8000
```

### Frontend (React)

The frontend is a single-page React application with Recharts visualizations.

```bash
cd src/gitflow/dashboard/frontend
npm install
npm start
```

Requires Node.js 18+. The dev server runs on `http://localhost:3000` and proxies API calls to the FastAPI backend.

**Dashboard Components:**
- Summary cards (today's commits, productivity score, lines added, weekly commits)
- Commits trend line chart (30 days)
- Productivity score trend line chart
- Repository breakdown bar chart
- Commit patterns panel (peak hour, best day, hot files)

> The dashboard is optional. The CLI works fully standalone without it.

---

## Database Schema

The SQLite database is stored at `~/.gitflow/gitflow.db` and is auto-created on first use.

| Table | Purpose |
|-------|---------|
| `repositories` | Tracked Git repositories |
| `commits` | Parsed commit data with stats |
| `commit_files` | Individual files changed per commit |
| `daily_stats` | Cached daily statistics |
| `weekly_stats` | Cached weekly summaries |
| `monthly_stats` | Cached monthly summaries |
| `commit_streaks` | Calculated streak records |
| `tasks_commits` | Optional task management links |
| `commit_annotations` | Commit labels (refactor, bug-fix, etc.) |

Indexes on: `committed_date`, `author`, `repo_id`, `(year, month)`.

---

## Productivity Score Algorithm

The score (0–100) is calculated daily with four weighted factors:

| Factor | Weight | Calculation |
|--------|--------|-------------|
| Commit Frequency | 30% | `min(100, commits / 5 * 100)` |
| Message Quality | 30% | 50% for conventional format + 50% for length (7–72 chars) |
| File Diversity | 20% | `min(100, unique_files / 20 * 100)` |
| Time Consistency | 20% | `unique_hours / 24 * 100` |

Scores above 100 are clamped.

---

## Background Service

The scheduler runs three automated jobs:

| Job | Schedule | Description |
|-----|----------|-------------|
| `scrape_repos` | Every hour at :00 | Fetches new commits from all tracked repos |
| `daily_stats` | Daily at 12:01 AM | Caches previous day's statistics |
| `daily_digest` | Daily at 8:00 AM | Sends desktop notification with digest |

Requires `plyer` for system notifications (`pip install -e ".[notifications]"`).

---

## Configuration

GitFlow uses no configuration file by default. The database path defaults to `~/.gitflow/gitflow.db`.

Environment variables (loaded from `.env` if present):

| Variable | Default | Description |
|----------|---------|-------------|
| `GITFLOW_DB_PATH` | `~/.gitflow/gitflow.db` | Database file location |

---

## Project Structure

```
GitFlow/
├── src/gitflow/
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy ORM models
│   ├── db.py                  # Database session management
│   ├── scraper/
│   │   └── git_scraper.py     # Git repository scanner
│   ├── analytics/
│   │   └── analytics_engine.py # Statistics & scoring engine
│   ├── cli/
│   │   ├── main.py            # Click CLI entry point
│   │   └── commands/
│   │       └── report.py      # Report subcommands
│   ├── scheduler/
│   │   └── background_service.py # APScheduler automation
│   └── dashboard/
│       ├── api/
│       │   └── main.py        # FastAPI application
│       └── frontend/
│           ├── public/
│           │   └── index.html
│           └── src/
│               ├── App.jsx
│               ├── index.jsx
│               └── components/
│                   └── Dashboard.jsx
├── setup.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Development

### Setup

```bash
# Editable install with dev dependencies
pip install -e ".[all]"

# Verify installation
gitflow --help
```

### Testing

```bash
# Run tests (when available)
pytest tests/
```

### Building

```bash
# Build wheel and source distribution
python -m build

# Install built package
pip install dist/gitflow-*.whl
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Repo` not found error | Ensure the path is a valid Git repository with commits |
| No commits found | Run `gitflow scan` first, or use `--since` with a broader range |
| Dashboard won't start | Install extras: `pip install -e ".[dashboard]"` |
| Notifications not working | Install extras: `pip install -e ".[notifications]"` |
| Database locked error | Only one process should access the DB at a time |

---

## License

MIT
