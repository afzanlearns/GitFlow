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
- **Configuration Management** — YAML-based config file with dot-notation access
- **Setup Wizard** — Interactive CLI setup for first-time configuration
- **Search & Filter API** — Full-text search and multi-dimensional filtering
- **API Authentication** — Token-based auth for dashboard endpoints
- **Docker Support** — Containerized deployment with docker-compose
- **Export Formats** — CSV, JSON, and Markdown export
- **Comprehensive Testing** — 40+ unit tests with >80% core coverage

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
| `--config PATH` | Path to config file (also via `GITFLOW_CONFIG` env var) |

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

Export commit data to CSV, JSON, or Markdown.

```bash
gitflow export --format csv --output my_commits
gitflow export --format json --output my_commits --days 90
gitflow export --format markdown --output report --days 30
```

CSV columns: date, author, message, files_changed, insertions, deletions, repository.
JSON: nested structure with full commit metadata.
Markdown: formatted table with summary header and per-commit rows.

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

#### `setup`

Interactive setup wizard for first-time configuration.

```bash
gitflow setup
```

Walks through:
1. Adding repositories to track (with validation)
2. Configuring notifications (email, Slack webhook)
3. Setting analytics thresholds
4. Choosing UI theme (dark/light)
5. Starting background service

#### `config-show`

Display current configuration values in a formatted table.

```bash
gitflow config-show
```

#### `config-set`

Set a configuration value using dot notation.

```bash
gitflow config-set gitflow.scrape_interval_hours 2
gitflow config-set notifications.slack_webhook https://hooks.slack.com/services/...
gitflow config-set ui.theme light
```

#### `config-reset`

Reset all configuration to factory defaults.

```bash
gitflow config-reset
```

#### `token generate`

Generate a new API authentication token for dashboard access.

```bash
gitflow token generate
```

#### `token show`

Display the current API token.

```bash
gitflow token show
```

#### `token revoke`

Invalidate the current API token.

```bash
gitflow token revoke
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
| `GET /api/search?q=&category=` | Search commits, files, or authors |
| `GET /api/filter?author=&repo=&days=&language=` | Multi-dimensional filtering with pagination |
| `GET /api/authors` | List all authors with commit counts |
| `GET /api/hot-files?days=` | Most-changed files in last N days |
| `GET /api/commit-by-language?days=` | Commits broken down by file language |
| `GET /api/health` | Health check |
| `WS /ws/live` | Real-time updates every 30 seconds |

All endpoints support optional Bearer token authentication via `Authorization: Bearer <token>` header.

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

GitFlow uses a YAML configuration file at `~/.gitflow/config.yml`, auto-created on first run with sensible defaults.

### Default Configuration

```yaml
gitflow:
  scrape_interval_hours: 1
  database_path: ~/.gitflow/gitflow.db

notifications:
  enabled: true
  slack_webhook: null
  email_enabled: false
  email_address: null

analytics:
  productivity_threshold: 80
  streak_reset_days: 1

scheduler:
  daily_stats_time: "00:01"
  daily_digest_time: "08:00"

ui:
  theme: "dark"
```

### CLI Management

```bash
# View current config
gitflow config-show

# Set a value (dot notation)
gitflow config-set gitflow.scrape_interval_hours 2

# Reset to defaults
gitflow config-reset
```

### Custom Config File

Use `--config` flag or `GITFLOW_CONFIG` environment variable:

```bash
gitflow --config /path/to/config.yml scan
export GITFLOW_CONFIG=/path/to/config.yml
gitflow report daily
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITFLOW_CONFIG` | `~/.gitflow/config.yml` | Path to config file |
| `GITFLOW_DB_PATH` | `~/.gitflow/gitflow.db` | Database file location |

---

## API Authentication

The dashboard API supports optional Bearer token authentication to protect endpoints.

### Managing Tokens

```bash
# Generate a new token
gitflow token generate
# Output: New API token generated: abc123...

# View current token
gitflow token show

# Revoke current token
gitflow token revoke
```

### Using Tokens

Include the token in API requests:

```bash
curl -H "Authorization: Bearer abc123..." http://localhost:8000/api/dashboard
```

Tokens are stored at `~/.gitflow/.api_token`. Authentication is optional — endpoints work without a token unless explicitly required.

---

## Docker Deployment

### Building

```bash
docker build -t gitflow .
```

### Running with Docker Compose

```bash
docker-compose up -d
```

### Mounting Repositories

Edit `docker-compose.yml` to mount your Git repositories:

```yaml
volumes:
  - /path/to/your/repos:/repos:ro
```

Then add repos inside the container:

```bash
docker-compose exec gitflow-scraper gitflow add /repos/myapp
```

### Container Management

```bash
docker-compose logs -f    # View logs
docker-compose down       # Stop service
docker-compose restart    # Restart service
```

The container runs the background service by default. The SQLite database persists in a Docker volume.

---

## Project Structure

```
GitFlow/
├── src/gitflow/
│   ├── __init__.py
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── db.py                      # Database session management
│   ├── config.py                  # YAML configuration management
│   ├── config.yml                 # Default config template
│   ├── scraper/
│   │   └── git_scraper.py         # Git repository scanner
│   ├── analytics/
│   │   └── analytics_engine.py    # Statistics & scoring engine
│   ├── cli/
│   │   ├── main.py                # Click CLI entry point
│   │   └── commands/
│   │       ├── report.py          # Report subcommands
│   │       └── setup.py           # Interactive setup wizard
│   ├── scheduler/
│   │   └── background_service.py  # APScheduler automation
│   └── dashboard/
│       ├── api/
│       │   ├── main.py            # FastAPI application
│       │   └── auth.py            # Token authentication
│       └── frontend/
│           ├── public/index.html
│           └── src/
│               ├── App.jsx
│               ├── index.jsx
│               └── components/Dashboard.jsx
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Test fixtures
│   ├── test_git_scraper.py        # Scraper tests (8 tests)
│   ├── test_analytics_engine.py   # Analytics tests (17 tests)
│   └── test_cli_commands.py       # CLI tests (15 tests)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── setup.py
├── pyproject.toml
├── requirements.txt
├── pytest.ini
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
# Run all tests with coverage
python -m pytest

# With coverage report
python -m pytest --cov=src.gitflow --cov-report=html

# Run specific test file
python -m pytest tests/test_analytics_engine.py -v
```

Current test suite: **40 tests** across 3 test files covering:
- `test_git_scraper.py` — Repository add, deduplication, commit parsing, scanning
- `test_analytics_engine.py` — Daily/weekly/monthly stats, caching, streaks, patterns, scoring
- `test_cli_commands.py` — All CLI commands via Click test runner

Coverage targets: >80% on core modules (analytics engine, models, db, scraper).

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
| Config file errors | Run `gitflow config-reset` to regenerate with defaults |
| API returns 401 | Run `gitflow token generate` and use the new token |
| Docker permission denied | Ensure mounted repo paths are readable by the container |
| Tests failing on Windows | Run `git config core.autocrlf true` before tests |

---

## License

MIT
