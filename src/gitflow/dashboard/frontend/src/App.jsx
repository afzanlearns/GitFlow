import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import './index.css';
import './App.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const [dashRes, histRes] = await Promise.all([
        axios.get('http://localhost:8000/api/dashboard'),
        axios.get('http://localhost:8000/api/history/30')
      ]);
      setStats(dashRes.data);
      setHistory(histRes.data.data || []);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="dashboard-container loading-state">
        <div className="loader">
          <div className="spinner"></div>
          <p>Loading GitFlow Dashboard...</p>
        </div>
      </div>
    );
  }

  const scoreColor = stats?.productivity_score >= 80 ? 'score-high' : 
                     stats?.productivity_score >= 60 ? 'score-medium' : 'score-low';

  return (
    <div className="dashboard-container">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <h1>❄️ GitFlow Dashboard</h1>
          <p className="subtitle">Git Analytics & Productivity Insights</p>
        </div>
        <div className="header-right">
          <button className="btn-refresh" onClick={fetchDashboard}>
            🔄 Refresh
          </button>
          <a href="http://localhost:8000/docs" className="btn-docs" target="_blank" rel="noopener noreferrer">
            📚 API Docs
          </a>
        </div>
      </header>

      {/* Last Updated */}
      <div className="last-updated">
        Last updated: {lastUpdated.toLocaleTimeString()} | 
        {stats?.today?.commit_count > 0 ? (
          <span className="status-badge online">🟢 API Connected</span>
        ) : (
          <span className="status-badge offline">🔴 No Data</span>
        )}
      </div>

      {/* Summary Cards Grid */}
      <div className="cards-grid">
        <StatCard
          title="TODAY'S COMMITS"
          value={stats?.today?.commit_count || 0}
          icon="📝"
          color="blue"
          trend={stats?.today?.commit_count > 5 ? '+' : ''}
        />
        <StatCard
          title="PRODUCTIVITY SCORE"
          value={`${Math.round(stats?.productivity_score || 0)}/100`}
          icon="📊"
          color="green"
          className={scoreColor}
        />
        <StatCard
          title="LINES ADDED"
          value={stats?.today?.lines_added || 0}
          icon="➕"
          color="green"
          subtext="insertions"
        />
        <StatCard
          title="LINES DELETED"
          value={stats?.today?.lines_deleted || 0}
          icon="➖"
          color="red"
          subtext="deletions"
        />
        <StatCard
          title="THIS WEEK"
          value={stats?.this_week?.total_commits || 0}
          icon="📅"
          color="purple"
          subtext="commits"
        />
        <StatCard
          title="FILES CHANGED"
          value={stats?.today?.files_touched || 0}
          icon="📁"
          color="orange"
          subtext="today"
        />
      </div>

      {/* Charts Section */}
      <div className="charts-section">
        {/* Row 1: Trends */}
        <div className="chart-card">
          <h3 className="chart-title">📈 Commit Trend (30 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="commitGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                labelStyle={{ color: '#f1f5f9' }}
              />
              <Line type="monotone" dataKey="commits" stroke="#06b6d4" strokeWidth={2} dot={{ fill: '#06b6d4', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">⭐ Productivity Score Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <defs>
                <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <YAxis domain={[0, 100]} stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                labelStyle={{ color: '#f1f5f9' }}
              />
              <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={2} dot={{ fill: '#10b981', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2: Repository & Patterns */}
      <div className="charts-section">
        <div className="chart-card">
          <h3 className="chart-title">📦 Repository Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.repositories || []} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="repository" stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <YAxis stroke="#94a3b8" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                labelStyle={{ color: '#f1f5f9' }}
              />
              <Legend wrapperStyle={{ color: '#94a3b8' }} />
              <Bar dataKey="commits" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              <Bar dataKey="lines_added" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="info-card patterns-card">
          <h3 className="chart-title">⚡ Commit Patterns</h3>
          <div className="patterns-grid">
            <div className="pattern-item">
              <span className="pattern-label">Peak Hour</span>
              <span className="pattern-value">{stats?.patterns?.peak_hour ? `${stats.patterns.peak_hour}:00 UTC` : '-'}</span>
            </div>
            <div className="pattern-item">
              <span className="pattern-label">Best Day</span>
              <span className="pattern-value">{stats?.patterns?.best_day || '-'}</span>
            </div>
            <div className="pattern-item">
              <span className="pattern-label">Most Changed File</span>
              <span className="pattern-value pattern-file">{stats?.patterns?.hot_files?.[0]?.path || '-'}</span>
            </div>
            <div className="pattern-item">
              <span className="pattern-label">Avg Session Time</span>
              <span className="pattern-value">~4.2h</span>
            </div>
          </div>

          {stats?.patterns?.hot_files && (
            <div className="hot-files">
              <h4>🔥 Hot Files This Month</h4>
              <ul>
                {stats.patterns.hot_files.slice(0, 5).map((file, i) => (
                  <li key={i}>
                    <span className="file-name">{file.path}</span>
                    <span className="file-changes">{file.changes} changes</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Repositories Table */}
      {stats?.repositories && stats.repositories.length > 0 && (
        <div className="table-card">
          <h3 className="chart-title">📚 Tracked Repositories</h3>
          <div className="table-wrapper">
            <table className="repos-table">
              <thead>
                <tr>
                  <th>Repository</th>
                  <th>Commits</th>
                  <th>Lines Added</th>
                  <th>Lines Deleted</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {stats.repositories.map((repo, i) => (
                  <tr key={i} className="table-row">
                    <td className="repo-name">{repo.repository}</td>
                    <td>{repo.commits}</td>
                    <td className="lines-added">+{repo.lines_added}</td>
                    <td className="lines-deleted">-{repo.lines_deleted}</td>
                    <td><span className="badge badge-tracked">tracked</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="dashboard-footer">
        <p>GitFlow — Real-time Git Analytics | Last sync: {lastUpdated.toLocaleTimeString()}</p>
      </footer>
    </div>
  );
}

function StatCard({ title, value, icon, color, subtext, className = '' }) {
  return (
    <div className={`stat-card stat-${color} ${className}`}>
      <div className="stat-icon">{icon}</div>
      <div className="stat-content">
        <div className="stat-label">{title}</div>
        <div className="stat-value">{value}</div>
        {subtext && <div className="stat-subtext">{subtext}</div>}
      </div>
    </div>
  );
}
