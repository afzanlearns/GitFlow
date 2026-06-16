"""
Fallback HTML dashboard served when the React build is not available.
Renders a basic but functional dark-mode dashboard that calls the API directly.
"""
from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitFlow Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-tertiary: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --accent-green: #10b981;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            --border-color: #334155;
            --shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1f35 100%);
            color: var(--text-primary);
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }

        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid var(--bg-secondary);
        }

        h1 {
            font-size: 32px;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 5px;
        }

        .subtitle {
            color: var(--text-muted);
            font-size: 14px;
        }

        .header-right {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
        }

        .btn-refresh {
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            color: white;
        }

        .btn-refresh:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }

        .btn-docs {
            background: var(--bg-secondary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }

        .btn-docs:hover {
            background: var(--bg-tertiary);
            border-color: var(--accent-cyan);
        }

        /* Last Updated */
        .last-updated {
            font-size: 12px;
            color: var(--text-muted);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }

        .status-badge.online {
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent-green);
        }

        /* Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(51, 65, 85, 0.5) 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan));
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .card:hover {
            border-color: var(--accent-cyan);
            transform: translateY(-5px);
            box-shadow: var(--shadow);
        }

        .card:hover::before {
            opacity: 1;
        }

        .card-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }

        .card-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--accent-cyan);
        }

        /* Table */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        thead {
            background: var(--bg-primary);
            border-bottom: 2px solid var(--border-color);
        }

        th {
            padding: 12px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            color: var(--text-muted);
        }

        td {
            padding: 12px;
            border-bottom: 1px solid var(--bg-tertiary);
        }

        tr:hover {
            background: var(--bg-tertiary);
        }

        /* Sections */
        .section {
            background: linear-gradient(135deg, var(--bg-secondary) 0%, rgba(51, 65, 85, 0.3) 100%);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }

        .section:hover {
            border-color: var(--accent-cyan);
            box-shadow: var(--shadow);
        }

        .section-title {
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text-primary);
        }

        .repo-path {
            font-size: 12px;
            color: var(--text-muted);
        }

        .status-tracked {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(16, 185, 129, 0.1);
            color: var(--accent-green);
        }

        .lines-added {
            color: var(--accent-green);
            font-weight: 600;
        }

        .lines-deleted {
            color: var(--accent-red);
            font-weight: 600;
        }

        /* Footer */
        footer {
            text-align: center;
            padding-top: 20px;
            border-top: 1px solid var(--border-color);
            color: var(--text-muted);
            font-size: 12px;
        }

        @media (max-width: 768px) {
            .container { padding: 15px; }
            h1 { font-size: 24px; }
            header { flex-direction: column; align-items: flex-start; gap: 15px; }
            .grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>❄️ GitFlow Dashboard</h1>
                <p class="subtitle">Git Analytics & Productivity Insights</p>
            </div>
            <div class="header-right">
                <button class="btn btn-refresh" onclick="location.reload()">🔄 Refresh</button>
                <a href="/docs" class="btn btn-docs" target="_blank">📚 API Docs</a>
            </div>
        </header>

        <div class="last-updated">
            Last updated: <span id="last-update"></span>
            <span class="status-badge online">🟢 API Connected</span>
        </div>

        <div class="grid" id="stats-container">
            <div class="card">
                <div class="card-label">Today's Commits</div>
                <div class="card-value" id="commits-today">-</div>
            </div>
            <div class="card">
                <div class="card-label">Productivity Score</div>
                <div class="card-value" id="score-today">-</div>
            </div>
            <div class="card">
                <div class="card-label">Lines Added</div>
                <div class="card-value" id="lines-added" style="color: var(--accent-green);">-</div>
            </div>
            <div class="card">
                <div class="card-label">Lines Deleted</div>
                <div class="card-value" id="lines-deleted" style="color: var(--accent-red);">-</div>
            </div>
            <div class="card">
                <div class="card-label">This Week</div>
                <div class="card-value" id="commits-week" style="color: var(--accent-orange);">-</div>
            </div>
            <div class="card">
                <div class="card-label">Files Changed</div>
                <div class="card-value" id="files-changed" style="color: var(--accent-blue);">-</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📦 Tracked Repositories</h2>
            <table id="repos-table">
                <thead>
                    <tr>
                        <th>Repository</th>
                        <th>Branch</th>
                        <th>Remote URL</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="repos-body">
                    <tr><td colspan="4" style="text-align: center; color: var(--text-muted);">Loading...</td></tr>
                </tbody>
            </table>
        </div>

        <footer>
            <p>GitFlow — Real-time Git Analytics & Productivity Tracking</p>
        </footer>
    </div>

    <script>
        async function loadDashboard() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();

                document.getElementById('commits-today').textContent = data.today?.commit_count || 0;
                document.getElementById('score-today').textContent = Math.round(data.productivity_score || 0);
                document.getElementById('lines-added').textContent = '+' + (data.today?.lines_added || 0);
                document.getElementById('lines-deleted').textContent = '-' + (data.today?.lines_deleted || 0);
                document.getElementById('commits-week').textContent = data.this_week?.total_commits || 0;
                document.getElementById('files-changed').textContent = data.today?.files_touched || 0;
                document.getElementById('last-update').textContent = new Date().toLocaleTimeString();

                const tbody = document.getElementById('repos-body');
                tbody.innerHTML = '';

                if (data.repositories && data.repositories.length > 0) {
                    data.repositories.forEach(repo => {
                        const row = tbody.insertRow();
                        row.innerHTML = `
                            <td><strong>${repo.repository}</strong></td>
                            <td>${repo.branch || '-'}</td>
                            <td><small>${repo.remote_url || '-'}</small></td>
                            <td><span class="status-tracked">tracked</span></td>
                        `;
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted);">No data yet. Run: gitflow scan</td></tr>';
                }
            } catch (error) {
                console.error('Error:', error);
            }
        }

        loadDashboard();
        setInterval(loadDashboard, 60000);
    </script>
</body>
</html>
"""


def get_html_dashboard() -> HTMLResponse:
    """Return the fallback HTML dashboard as an HTMLResponse."""
    return HTMLResponse(content=DASHBOARD_HTML)
