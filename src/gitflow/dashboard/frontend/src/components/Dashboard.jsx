import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const API_BASE = 'http://localhost:8000';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/dashboard`);
      const histRes = await axios.get(`${API_BASE}/api/history/30`);
      setStats(res.data);
      setHistory(histRes.data.data);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  };

  if (!stats) return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-xl text-gray-500">Loading dashboard...</div>
    </div>
  );

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-4xl font-bold mb-8">GitFlow Dashboard</h1>

      <div className="grid grid-cols-4 gap-4 mb-8">
        <Card label="Today's Commits" value={stats.today.commit_count} />
        <Card label="Productivity Score" value={`${stats.productivity_score.toFixed(0)}/100`} />
        <Card label="Lines Added" value={stats.today.lines_added} />
        <Card label="Weekly Commits" value={stats.this_week.total_commits || 0} />
      </div>

      <div className="grid grid-cols-2 gap-8 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Commits Trend (30 days)</h2>
          <LineChart width={500} height={300} data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="commits" stroke="#3b82f6" name="Commits" />
          </LineChart>
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Productivity Trend</h2>
          <LineChart width={500} height={300} data={history}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="score" stroke="#10b981" name="Score" />
          </LineChart>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Repository Breakdown</h2>
          {stats.repositories.length > 0 ? (
            <BarChart width={500} height={300} data={stats.repositories.map(r => ({
              name: r.repository,
              commits: r.commits,
              added: r.lines_added,
              deleted: r.lines_deleted
            }))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="commits" fill="#3b82f6" name="Commits" />
              <Bar dataKey="added" fill="#10b981" name="Lines Added" />
            </BarChart>
          ) : (
            <p className="text-gray-400">No repository data available</p>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Commit Patterns</h2>
          {stats.patterns && (
            <div className="space-y-3">
              {stats.patterns.peak_hour && (
                <div>
                  <span className="text-gray-600">Peak Hour:</span>
                  <span className="ml-2 font-semibold">{stats.patterns.peak_hour}:00 UTC</span>
                </div>
              )}
              {stats.patterns.best_day && (
                <div>
                  <span className="text-gray-600">Best Day:</span>
                  <span className="ml-2 font-semibold">{stats.patterns.best_day}</span>
                </div>
              )}
              {stats.patterns.hot_files && stats.patterns.hot_files.length > 0 && (
                <div>
                  <span className="text-gray-600 block mb-2">Most Changed Files:</span>
                  <ul className="list-disc pl-5 space-y-1">
                    {stats.patterns.hot_files.map((f, i) => (
                      <li key={i} className="text-sm">
                        {f.path} <span className="text-gray-400">({f.changes} changes)</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Card({ label, value }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="text-gray-600 text-sm">{label}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
}
