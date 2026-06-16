"""
Fallback HTML dashboard served when the React build is not available.
Renders a basic but functional dark-mode dashboard that calls the API directly.
"""
from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GitFlow Dashboard</title>
  <meta name="description" content="GitFlow – Git commit analytics and productivity dashboard" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #0f172a;
      --surface:   #1e293b;
      --border:    #334155;
      --muted:     #64748b;
      --subtle:    #94a3b8;
      --text:      #e2e8f0;
      --accent:    #38bdf8;
      --green:     #10b981;
      --red:       #ef4444;
      --amber:     #f59e0b;
      --purple:    #a78bfa;
      --radius:    10px;
    }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
    }

    /* ── Layout ── */
    .app { display: flex; flex-direction: column; min-height: 100vh; }

    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 0 2rem;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    header .logo {
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--accent);
      display: flex;
      align-items: center;
      gap: .5rem;
    }

    header .controls { display: flex; align-items: center; gap: 1rem; }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: .35rem;
      padding: .25rem .75rem;
      border-radius: 9999px;
      font-size: .75rem;
      font-weight: 600;
    }

    .badge-green  { background: rgba(16,185,129,.15); color: var(--green); }
    .badge-red    { background: rgba(239,68,68,.15);  color: var(--red);   }

    main { flex: 1; padding: 2rem; max-width: 1400px; margin: 0 auto; width: 100%; }

    /* ── Stat cards ── */
    .stat-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 1rem;
      margin-bottom: 2rem;
    }

    .stat-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.25rem 1.5rem;
      transition: border-color .2s, transform .2s;
    }

    .stat-card:hover { border-color: var(--accent); transform: translateY(-2px); }

    .stat-label { font-size: .75rem; color: var(--subtle); text-transform: uppercase; letter-spacing: .05em; margin-bottom: .5rem; }

    .stat-value { font-size: 2rem; font-weight: 700; line-height: 1; }

    .stat-value.green  { color: var(--green); }
    .stat-value.accent { color: var(--accent); }
    .stat-value.amber  { color: var(--amber); }
    .stat-value.purple { color: var(--purple); }

    /* ── Panels ── */
    .panels { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
    @media (max-width: 900px) { .panels { grid-template-columns: 1fr; } }

    .panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 1.5rem;
    }

    .panel-title {
      font-size: .875rem;
      font-weight: 600;
      color: var(--subtle);
      text-transform: uppercase;
      letter-spacing: .05em;
      margin-bottom: 1.25rem;
    }

    /* ── Table ── */
    table { width: 100%; border-collapse: collapse; }
    th { font-size: .7rem; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: .5rem .75rem; text-align: left; border-bottom: 1px solid var(--border); }
    td { padding: .65rem .75rem; font-size: .875rem; border-bottom: 1px solid rgba(51,65,85,.5); }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255,255,255,.02); }

    .text-green  { color: var(--green);  }
    .text-red    { color: var(--red);    }
    .text-muted  { color: var(--muted);  }
    .text-accent { color: var(--accent); }

    /* ── Mini bar chart ── */
    .bar-row { display: flex; align-items: center; gap: .75rem; margin-bottom: .5rem; }
    .bar-label { font-size: .75rem; color: var(--subtle); width: 6rem; flex-shrink: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .bar-track { flex: 1; background: var(--bg); border-radius: 3px; height: 6px; }
    .bar-fill  { height: 6px; border-radius: 3px; background: var(--accent); transition: width .4s; }
    .bar-count { font-size: .7rem; color: var(--muted); width: 2.5rem; text-align: right; }

    /* ── Patterns ── */
    .pattern-item { display: flex; justify-content: space-between; align-items: center; padding: .5rem 0; border-bottom: 1px solid rgba(51,65,85,.4); }
    .pattern-item:last-child { border-bottom: none; }
    .pattern-key { font-size: .8rem; color: var(--subtle); }
    .pattern-val { font-size: .875rem; font-weight: 600; }

    /* ── Buttons ── */
    .btn {
      display: inline-flex;
      align-items: center;
      gap: .4rem;
      padding: .45rem 1rem;
      border-radius: 6px;
      font-size: .8rem;
      font-weight: 500;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text);
      cursor: pointer;
      transition: background .15s, border-color .15s;
    }
    .btn:hover { background: var(--surface); border-color: var(--accent); color: var(--accent); }

    /* ── Toast / notices ── */
    .notice {
      background: rgba(16,185,129,.1);
      border: 1px solid rgba(16,185,129,.3);
      border-radius: var(--radius);
      padding: .75rem 1.25rem;
      font-size: .8rem;
      color: var(--green);
      margin-bottom: 1.5rem;
    }

    .notice.warn {
      background: rgba(245,158,11,.1);
      border-color: rgba(245,158,11,.3);
      color: var(--amber);
    }

    /* ── Skeleton loading ── */
    .skeleton {
      background: linear-gradient(90deg, var(--surface) 25%, var(--border) 50%, var(--surface) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.4s infinite;
      border-radius: 4px;
      height: 1.5rem;
      width: 4rem;
      display: inline-block;
    }

    @keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }

    /* ── Footer ── */
    footer {
      padding: 1rem 2rem;
      text-align: center;
      font-size: .7rem;
      color: var(--muted);
      border-top: 1px solid var(--border);
    }
  </style>
</head>
<body>
<div class="app">

  <header>
    <div class="logo">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>
      GitFlow Dashboard
    </div>
    <div class="controls">
      <span id="api-status" class="badge badge-green">● API connected</span>
      <button class="btn" onclick="refresh()">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></svg>
        Refresh
      </button>
      <a href="/docs" class="btn" target="_blank">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        API Docs
      </a>
    </div>
  </header>

  <main>
    <div id="notice-fallback" class="notice warn" style="display:none">
      ℹ️ Serving HTML fallback dashboard. To get the full React UI run:
      <code style="background:rgba(0,0,0,.3);padding:2px 6px;border-radius:3px;">cd src/gitflow/dashboard/frontend &amp;&amp; npm install &amp;&amp; npm run build</code>
    </div>

    <!-- Stat cards -->
    <div class="stat-grid" id="stat-grid">
      <div class="stat-card"><div class="stat-label">Today's Commits</div><div class="stat-value green" id="stat-commits-today"><span class="skeleton"></span></div></div>
      <div class="stat-card"><div class="stat-label">Productivity Score</div><div class="stat-value accent" id="stat-score"><span class="skeleton"></span></div></div>
      <div class="stat-card"><div class="stat-label">Lines Added Today</div><div class="stat-value green" id="stat-lines-added"><span class="skeleton"></span></div></div>
      <div class="stat-card"><div class="stat-label">Lines Deleted Today</div><div class="stat-value" id="stat-lines-deleted" style="color:var(--red)"><span class="skeleton"></span></div></div>
      <div class="stat-card"><div class="stat-label">This Week Commits</div><div class="stat-value purple" id="stat-week-commits"><span class="skeleton"></span></div></div>
      <div class="stat-card"><div class="stat-label">Files Changed Today</div><div class="stat-value amber" id="stat-files-changed"><span class="skeleton"></span></div></div>
    </div>

    <!-- Middle panels -->
    <div class="panels">
      <!-- Repos breakdown -->
      <div class="panel">
        <div class="panel-title">Repository Breakdown (30 days)</div>
        <div id="repos-bars"><div style="color:var(--muted);font-size:.8rem">Loading…</div></div>
      </div>

      <!-- Patterns -->
      <div class="panel">
        <div class="panel-title">Commit Patterns</div>
        <div id="patterns-panel"><div style="color:var(--muted);font-size:.8rem">Loading…</div></div>
      </div>
    </div>

    <!-- Full repos table -->
    <div class="panel">
      <div class="panel-title">Tracked Repositories</div>
      <table>
        <thead><tr><th>Repository</th><th>Commits</th><th>Lines Added</th><th>Lines Deleted</th></tr></thead>
        <tbody id="repos-tbody"><tr><td colspan="4" class="text-muted">Loading…</td></tr></tbody>
      </table>
    </div>
  </main>

  <footer>GitFlow · Fallback Dashboard · <a href="/docs" style="color:var(--accent)">API Docs ↗</a> · Auto-refreshes every 60 s</footer>
</div>

<script>
  let maxRepoCommits = 1;

  async function refresh() {
    try {
      const [dashRes, reposRes] = await Promise.all([
        fetch('/api/dashboard'),
        fetch('/api/repos'),
      ]);

      if (!dashRes.ok) throw new Error(`/api/dashboard returned ${dashRes.status}`);
      const d   = await dashRes.json();
      const repos = reposRes.ok ? await reposRes.json() : [];

      document.getElementById('api-status').className = 'badge badge-green';
      document.getElementById('api-status').textContent = '● API connected';

      // Stat cards
      setText('stat-commits-today', d.today?.commit_count ?? 0);
      setText('stat-score',         Math.round(d.productivity_score ?? 0) + ' / 100');
      setText('stat-lines-added',   '+' + (d.today?.lines_added ?? 0));
      setText('stat-lines-deleted', '-' + (d.today?.lines_deleted ?? 0));
      setText('stat-week-commits',  d.this_week?.total_commits ?? 0);
      setText('stat-files-changed', d.today?.files_changed ?? 0);

      // Repository bar chart
      const repoBars = document.getElementById('repos-bars');
      const repData  = d.repositories ?? [];
      if (repData.length === 0) {
        repoBars.innerHTML = '<div style="color:var(--muted);font-size:.8rem">No repository data. Run <code>gitflow scan</code>.</div>';
      } else {
        maxRepoCommits = Math.max(...repData.map(r => r.commits), 1);
        repoBars.innerHTML = repData.map(r => `
          <div class="bar-row">
            <span class="bar-label" title="${r.repository}">${r.repository}</span>
            <div class="bar-track"><div class="bar-fill" style="width:${Math.round(r.commits/maxRepoCommits*100)}%"></div></div>
            <span class="bar-count">${r.commits}</span>
          </div>`).join('');
      }

      // Patterns panel
      const pat = d.patterns ?? {};
      const patEl = document.getElementById('patterns-panel');
      const items = [];
      if (pat.peak_hour != null) items.push(['Peak Commit Hour', pat.peak_hour + ':00 UTC']);
      if (pat.best_day)         items.push(['Most Active Day',   pat.best_day]);
      if (pat.hot_files?.length) items.push(['Hottest File',     pat.hot_files[0]?.path ?? '—']);
      if (items.length === 0)   items.push(['Status', 'Not enough data yet']);
      patEl.innerHTML = items.map(([k,v]) => `
        <div class="pattern-item">
          <span class="pattern-key">${k}</span>
          <span class="pattern-val text-accent">${v}</span>
        </div>`).join('');

      // Full repos table
      const tbody = document.getElementById('repos-tbody');
      if (repos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-muted">No repositories tracked. Run <code>gitflow add &lt;path&gt;</code>.</td></tr>';
      } else {
        tbody.innerHTML = repos.map(r => `
          <tr>
            <td><strong>${r.name}</strong><br/><span class="text-muted" style="font-size:.7rem">${r.path}</span></td>
            <td>${r.branch ?? '—'}</td>
            <td>${r.remote_url ?? '—'}</td>
            <td><span class="badge badge-green">tracked</span></td>
          </tr>`).join('');
      }

    } catch (err) {
      document.getElementById('api-status').className = 'badge badge-red';
      document.getElementById('api-status').textContent = '● API error';
      console.error('Dashboard fetch error:', err);
    }
  }

  function setText(id, val) {
    document.getElementById(id).textContent = val;
  }

  // Show fallback notice
  document.getElementById('notice-fallback').style.display = 'block';

  // Initial load + interval
  refresh();
  setInterval(refresh, 60000);
</script>
</body>
</html>
"""


def get_html_dashboard() -> HTMLResponse:
    """Return the fallback HTML dashboard as an HTMLResponse."""
    return HTMLResponse(content=DASHBOARD_HTML)
