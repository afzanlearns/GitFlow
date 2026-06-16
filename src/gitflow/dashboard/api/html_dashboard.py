"""
Fallback HTML dashboard served when the React build is not available.
Matches the React dashboard design: Vercel-inspired, light/dark mode, Chart.js.
"""
from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitFlow</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f5f5f5;
            --bg-tertiary: #eeeeee;

            --text-primary: #0a0a0a;
            --text-secondary: #525252;
            --text-tertiary: #737373;

            --border-color: #e5e5e5;
            --border-light: #f5f5f5;

            --accent-primary: #0070f3;
            --accent-success: #0cce6b;
            --accent-error: #ff0080;
            --accent-warning: #f5a623;

            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
            --shadow-md: 0 3px 6px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0, 0, 0, 0.12);
            --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.15), 0 3px 6px rgba(0, 0, 0, 0.10);
        }

        html.dark-mode {
            --bg-primary: #0a0a0a;
            --bg-secondary: #161616;
            --bg-tertiary: #262626;

            --text-primary: #ffffff;
            --text-secondary: #b3b3b3;
            --text-tertiary: #888888;

            --border-color: #333333;
            --border-light: #1a1a1a;

            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
            --shadow-md: 0 3px 6px rgba(0, 0, 0, 0.3);
            --shadow-lg: 0 10px 20px rgba(0, 0, 0, 0.3);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        html {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            color: var(--text-primary);
            background: var(--bg-primary);
            transition: background-color 200ms, color 200ms;
        }

        body { line-height: 1.5; }

        code, pre, .monospace {
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
        }

        button {
            font-family: inherit;
            cursor: pointer;
            transition: all 200ms;
        }

        a {
            color: var(--accent-primary);
            text-decoration: none;
            transition: opacity 200ms;
        }

        a:hover { opacity: 0.7; }

        table { border-collapse: collapse; }

        .header {
            border-bottom: 1px solid var(--border-color);
            padding: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-primary);
            transition: border-color 200ms;
        }

        .header-left { display: flex; flex-direction: column; gap: 4px; }

        .logo {
            font-size: 20px;
            font-weight: 600;
            letter-spacing: -0.5px;
            color: var(--text-primary);
        }

        .tagline {
            font-size: 12px;
            color: var(--text-tertiary);
            letter-spacing: 0.5px;
        }

        .header-right { display: flex; gap: 12px; align-items: center; }

        .btn {
            padding: 8px 16px;
            border: 1px solid var(--border-color);
            background: var(--bg-primary);
            color: var(--text-primary);
            border-radius: 4px;
            font-size: 13px;
            font-weight: 500;
            white-space: nowrap;
            transition: all 200ms;
        }

        .btn:hover {
            border-color: var(--text-secondary);
            box-shadow: var(--shadow-sm);
        }

        .btn-refresh {
            background: var(--accent-primary);
            color: white;
            border-color: var(--accent-primary);
        }

        .btn-refresh:hover { opacity: 0.9; }

        .btn-theme {
            width: 36px; height: 36px; padding: 0;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
        }

        .btn-docs {
            color: var(--accent-primary);
            border-color: var(--accent-primary);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 32px 24px;
        }

        .last-updated {
            font-size: 12px;
            color: var(--text-tertiary);
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
        }

        .status-badge {
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .status-badge.online {
            background: rgba(12, 206, 107, 0.1);
            color: var(--accent-success);
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
            margin-bottom: 32px;
        }

        .stat-card {
            padding: 16px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            transition: all 200ms;
        }

        .stat-card:hover {
            border-color: var(--text-secondary);
            box-shadow: var(--shadow-sm);
        }

        .stat-label {
            font-size: 12px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .stat-value {
            font-size: 28px;
            font-weight: 600;
            color: var(--text-primary);
            letter-spacing: -0.5px;
        }

        .stat-subtext {
            font-size: 12px;
            color: var(--text-tertiary);
            margin-top: 4px;
        }

        .stat-card.score-high .stat-value { color: var(--accent-success); }
        .stat-card.score-medium .stat-value { color: var(--accent-warning); }
        .stat-card.score-low .stat-value { color: var(--accent-error); }
        .stat-card.stat-positive .stat-value { color: var(--accent-success); }
        .stat-card.stat-negative .stat-value { color: var(--accent-error); }

        .charts-section {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
            margin-bottom: 32px;
        }

        .chart-container {
            padding: 24px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            transition: all 200ms;
        }

        .chart-container:hover {
            border-color: var(--text-secondary);
            box-shadow: var(--shadow-sm);
        }

        .chart-container.full-width { grid-column: 1 / -1; }

        .chart-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            letter-spacing: -0.2px;
        }

        .chart-canvas {
            position: relative;
            height: 280px;
        }

        .section {
            padding: 24px;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            margin-bottom: 24px;
            transition: all 200ms;
        }

        .section:hover {
            border-color: var(--text-secondary);
            box-shadow: var(--shadow-sm);
        }

        .section-title {
            font-size: 14px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
            letter-spacing: -0.2px;
        }

        .repo-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .repo-table thead { border-bottom: 1px solid var(--border-color); }

        .repo-table th {
            padding: 12px 8px;
            text-align: left;
            font-weight: 500;
            color: var(--text-tertiary);
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }

        .repo-table td {
            padding: 12px 8px;
            border-bottom: 1px solid var(--border-light);
            color: var(--text-secondary);
        }

        .repo-table tbody tr:hover { background: var(--bg-secondary); }

        .cell-repo { color: var(--text-primary); font-weight: 500; }

        .cell-branch {
            font-family: 'Menlo', 'Monaco', monospace;
            color: var(--accent-primary);
            font-size: 12px;
        }

        .cell-url {
            font-family: 'Menlo', 'Monaco', monospace;
            color: var(--text-tertiary);
            font-size: 12px;
            word-break: break-all;
        }

        .cell-commits { font-weight: 600; color: var(--text-primary); }

        .empty {
            text-align: center;
            color: var(--text-tertiary);
            padding: 24px !important;
        }

        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }

        .insight-card {
            padding: 12px;
            background: var(--bg-secondary);
            border-radius: 4px;
            border: 1px solid var(--border-color);
        }

        .insight-label {
            font-size: 11px;
            color: var(--text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
            font-weight: 500;
        }

        .insight-value {
            font-size: 13px;
            color: var(--text-primary);
            font-weight: 500;
        }

        .insight-value.code {
            font-family: 'Menlo', 'Monaco', monospace;
            font-size: 11px;
            color: var(--accent-primary);
            word-break: break-all;
        }

        .footer {
            border-top: 1px solid var(--border-color);
            padding: 24px;
            text-align: center;
            color: var(--text-tertiary);
            font-size: 13px;
        }

        .footer p { margin: 4px 0; }

        .footer-meta {
            font-family: 'Menlo', 'Monaco', monospace;
            font-size: 12px;
        }

        @media (max-width: 1024px) {
            .charts-section { grid-template-columns: 1fr; }
        }

        @media (max-width: 768px) {
            .header { padding: 16px; gap: 16px; flex-direction: column; align-items: flex-start; }
            .header-right { width: 100%; gap: 8px; }
            .container { padding: 16px 12px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
            .stat-card { padding: 12px; }
            .stat-value { font-size: 20px; }
            .charts-section { grid-template-columns: 1fr; gap: 16px; }
            .chart-container { padding: 16px; }
            .insights-grid { grid-template-columns: 1fr; }
            .repo-table { font-size: 12px; }
            .repo-table th, .repo-table td { padding: 8px 4px; }
        }
    </style>
</head>
<body>
    <header class="header">
        <div class="header-left">
            <div class="logo">GitFlow</div>
            <div class="tagline">Git Analytics</div>
        </div>
        <div class="header-right">
            <button class="btn btn-refresh" onclick="location.reload()" title="Refresh data">Refresh</button>
            <button class="btn btn-theme" onclick="toggleTheme()" title="Toggle theme" aria-label="Toggle theme">
                <span id="theme-icon">\u263E</span>
            </button>
            <a href="/docs" class="btn btn-docs" target="_blank" rel="noopener noreferrer">API Docs</a>
        </div>
    </header>

    <div class="container">
        <div class="last-updated">
            Last updated: <span id="last-update">-</span>
            <span class="status-badge online">API Connected</span>
        </div>

        <div class="stats-grid" id="stats-container">
            <div class="stat-card">
                <div class="stat-label">Today's Commits</div>
                <div class="stat-value" id="commits-today">-</div>
            </div>
            <div class="stat-card" id="score-card">
                <div class="stat-label">Productivity Score</div>
                <div class="stat-value" id="score-today">-</div>
                <div class="stat-subtext">/100</div>
            </div>
            <div class="stat-card stat-positive">
                <div class="stat-label">Lines Added</div>
                <div class="stat-value" id="lines-added">-</div>
                <div class="stat-subtext">insertions</div>
            </div>
            <div class="stat-card stat-negative">
                <div class="stat-label">Lines Deleted</div>
                <div class="stat-value" id="lines-deleted">-</div>
                <div class="stat-subtext">deletions</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">This Week</div>
                <div class="stat-value" id="commits-week">-</div>
                <div class="stat-subtext">commits</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Files Changed</div>
                <div class="stat-value" id="files-changed">-</div>
                <div class="stat-subtext">today</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="chart-container">
                <div class="chart-title">Commit Trend</div>
                <div class="chart-canvas">
                    <canvas id="commitChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <div class="chart-title">Productivity Score</div>
                <div class="chart-canvas">
                    <canvas id="scoreChart"></canvas>
                </div>
            </div>

            <div class="chart-container full-width">
                <div class="chart-title">Repository Breakdown</div>
                <div class="chart-canvas" style="height: 300px;">
                    <canvas id="repoChart"></canvas>
                </div>
            </div>
        </div>

        <div class="section" id="insights-section" style="display: none;">
            <div class="section-title">Insights</div>
            <div class="insights-grid">
                <div class="insight-card">
                    <div class="insight-label">Peak Hour</div>
                    <div class="insight-value" id="peak-hour">-</div>
                </div>
                <div class="insight-card">
                    <div class="insight-label">Most Active Day</div>
                    <div class="insight-value" id="active-day">-</div>
                </div>
                <div class="insight-card">
                    <div class="insight-label">Hot File</div>
                    <div class="insight-value code" id="hot-file">-</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">Repositories</div>
            <table class="repo-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Branch</th>
                        <th>Remote URL</th>
                        <th>Commits</th>
                    </tr>
                </thead>
                <tbody id="repos-body">
                    <tr>
                        <td colspan="4" class="empty">Loading...</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <footer class="footer">
        <p>GitFlow — Real-time Git Analytics</p>
        <p class="footer-meta">Last sync: <span id="footer-time">-</span></p>
    </footer>

    <script>
        // ========== THEME TOGGLE ==========
        function toggleTheme() {
            var isDark = document.documentElement.classList.contains('dark-mode');
            if (isDark) {
                document.documentElement.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'false');
                document.getElementById('theme-icon').textContent = '\\u263E';
            } else {
                document.documentElement.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'true');
                document.getElementById('theme-icon').textContent = '\\u2600';
            }
            updateCharts();
        }

        // Load theme preference
        if (localStorage.getItem('darkMode') === 'true') {
            document.documentElement.classList.add('dark-mode');
            document.getElementById('theme-icon').textContent = '\\u2600';
        }

        // ========== CHART COLOR HELPERS ==========
        function getChartColors() {
            var isDark = document.documentElement.classList.contains('dark-mode');
            return {
                text: isDark ? '#ffffff' : '#0a0a0a',
                border: isDark ? '#333333' : '#e5e5e5',
                grid: isDark ? 'rgba(51, 51, 51, 0.1)' : 'rgba(229, 229, 229, 0.5)',
            };
        }

        // ========== CHART INSTANCES ==========
        var commitChart, scoreChart, repoChart;

        function createCharts() {
            var colors = getChartColors();
            var baseOpts = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: colors.text,
                            font: { size: 12, family: 'system-ui' },
                            padding: 16,
                            usePointStyle: true,
                        },
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: colors.border,
                        borderWidth: 1,
                        padding: 12,
                    },
                },
                scales: {
                    x: {
                        grid: { color: colors.grid, drawBorder: false },
                        ticks: { color: colors.text, font: { size: 12 } },
                    },
                    y: {
                        grid: { color: colors.grid, drawBorder: false },
                        ticks: { color: colors.text, font: { size: 12 } },
                        beginAtZero: true,
                    },
                },
            };

            commitChart = new Chart(document.getElementById('commitChart'), {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: baseOpts,
            });

            scoreChart = new Chart(document.getElementById('scoreChart'), {
                type: 'line',
                data: { labels: [], datasets: [] },
                options: baseOpts,
            });

            repoChart = new Chart(document.getElementById('repoChart'), {
                type: 'bar',
                data: { labels: [], datasets: [] },
                options: baseOpts,
            });
        }

        function updateCharts() {
            if (!commitChart) return;
            var colors = getChartColors();
            var chartOpts = {
                plugins: { legend: { labels: { color: colors.text } } },
                scales: {
                    x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                    y: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                },
            };
            commitChart.options = Object.assign(commitChart.options, chartOpts);
            scoreChart.options = Object.assign(scoreChart.options, chartOpts);
            repoChart.options = Object.assign(repoChart.options, chartOpts);
            commitChart.update();
            scoreChart.update();
            repoChart.update();
        }

        // ========== DATA FETCHING ==========
        async function loadDashboard() {
            try {
                var [dashRes, histRes, reposRes] = await Promise.all([
                    fetch('/api/dashboard'),
                    fetch('/api/history/30'),
                    fetch('/api/repos')
                ]);
                var data = await dashRes.json();
                var histData = await histRes.json();
                var reposList = await reposRes.json();

                // Build repos map for branch/remote_url
                var reposMap = {};
                (reposList || []).forEach(function(r) {
                    reposMap[r.name] = r;
                });

                // Stats
                document.getElementById('commits-today').textContent = data.today?.commit_count || 0;
                var score = Math.round(data.productivity_score || 0);
                document.getElementById('score-today').textContent = score;
                document.getElementById('lines-added').textContent = data.today?.lines_added || 0;
                document.getElementById('lines-deleted').textContent = data.today?.lines_deleted || 0;
                document.getElementById('commits-week').textContent = data.this_week?.total_commits || 0;
                document.getElementById('files-changed').textContent = data.today?.files_touched || 0;

                // Score color coding
                var scoreCard = document.getElementById('score-card');
                scoreCard.classList.remove('score-low', 'score-medium', 'score-high');
                if (score >= 80) scoreCard.classList.add('score-high');
                else if (score >= 60) scoreCard.classList.add('score-medium');
                else scoreCard.classList.add('score-low');

                // Timestamps
                var now = new Date();
                document.getElementById('last-update').textContent = now.toLocaleTimeString();
                document.getElementById('footer-time').textContent = now.toLocaleTimeString();

                // Charts
                updateChartsData(histData.data || []);

                // Insights
                if (data.patterns) {
                    document.getElementById('insights-section').style.display = 'block';
                    document.getElementById('peak-hour').textContent = data.patterns.peak_hour ? data.patterns.peak_hour + ':00 UTC' : '-';
                    document.getElementById('active-day').textContent = data.patterns.best_day || '-';
                    document.getElementById('hot-file').textContent = (data.patterns.hot_files && data.patterns.hot_files[0]) ? data.patterns.hot_files[0].path : '-';
                }

                // Repositories table
                var tbody = document.getElementById('repos-body');
                tbody.innerHTML = '';

                if (data.repositories && data.repositories.length > 0) {
                    data.repositories.forEach(function(repo) {
                        var repoMeta = reposMap[repo.repository] || {};
                        var row = tbody.insertRow();
                        row.innerHTML =
                            '<td class="cell-repo">' + (repo.repository || '') + '</td>' +
                            '<td class="cell-branch">' + (repoMeta.branch || '-') + '</td>' +
                            '<td class="cell-url">' + (repoMeta.remote_url || '-') + '</td>' +
                            '<td class="cell-commits">' + (repo.commits || 0) + '</td>';
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="4" class="empty">No data yet. Run: gitflow scan</td></tr>';
                }
            } catch (error) {
                console.error('Error loading dashboard:', error);
            }
        }

        function updateChartsData(history) {
            if (!commitChart) return;

            var labels = history.map(function(h) { return h.date; });
            var commits = history.map(function(h) { return h.commits || 0; });
            var scores = history.map(function(h) { return h.score || 0; });

            commitChart.data.labels = labels;
            commitChart.data.datasets = [{
                label: 'Commits',
                data: commits,
                borderColor: '#0070f3',
                backgroundColor: 'rgba(0, 112, 243, 0.05)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#0070f3',
                pointBorderWidth: 2,
            }];
            commitChart.update();

            scoreChart.data.labels = labels;
            scoreChart.data.datasets = [{
                label: 'Score',
                data: scores,
                borderColor: '#0cce6b',
                backgroundColor: 'rgba(12, 206, 107, 0.05)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#0cce6b',
                pointBorderWidth: 2,
            }];
            scoreChart.update();
        }

        // ========== INITIALIZATION ==========
        createCharts();
        loadDashboard();
        setInterval(loadDashboard, 60000);
    </script>
</body>
</html>
"""


def get_html_dashboard() -> HTMLResponse:
    """Return the fallback HTML dashboard as an HTMLResponse."""
    return HTMLResponse(content=DASHBOARD_HTML)
