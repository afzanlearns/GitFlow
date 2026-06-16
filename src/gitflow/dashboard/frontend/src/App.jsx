import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';
import Header from './components/Header';
import StatsGrid from './components/StatsGrid';
import Charts from './components/Charts';
import RepositoryInfo from './components/RepositoryInfo';
import './App.css';

export default function App() {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [repos, setRepos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('darkMode') === 'true'
  );

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.remove('dark-mode');
    }
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]);

  useEffect(() => {
    fetchDashboard();
    const interval = setInterval(fetchDashboard, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboard = async () => {
    try {
      setLoading(true);
      const [dashRes, histRes, reposRes] = await Promise.all([
        axios.get('/api/dashboard'),
        axios.get('/api/history/30'),
        axios.get('/api/repos')
      ]);
      setStats(dashRes.data);
      setHistory(histRes.data.data || []);

      const reposMap = {};
      (reposRes.data || []).forEach(r => {
        reposMap[r.name] = r;
      });

      const mergedRepos = (dashRes.data.repositories || []).map(r => ({
        ...r,
        branch: reposMap[r.repository]?.branch || null,
        remote_url: reposMap[r.repository]?.remote_url || null
      }));

      setRepos(mergedRepos);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="app loading-state">
        <div className="loader">
          <div className="spinner"></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
        onRefresh={fetchDashboard}
      />

      <main className="app-main">
        <StatsGrid stats={stats} />

        <Charts stats={stats} history={history} />

        <RepositoryInfo repos={repos} patterns={stats?.patterns} />
      </main>

      <footer className="app-footer">
        <p>GitFlow — Real-time Git Analytics</p>
        <p className="footer-meta">Last sync: {new Date().toLocaleTimeString()}</p>
      </footer>
    </div>
  );
}
