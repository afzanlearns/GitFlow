import React from 'react';
import './StatsGrid.css';

export default function StatsGrid({ stats }) {
  if (!stats) return null;

  const scoreColor = stats.productivity_score >= 80 ? 'high' :
                     stats.productivity_score >= 60 ? 'medium' : 'low';

  return (
    <div className="stats-grid">
      <StatCard
        label="Today's Commits"
        value={stats.today?.commit_count || 0}
      />
      <StatCard
        label="Productivity Score"
        value={`${Math.round(stats.productivity_score || 0)}`}
        subtext="/100"
        className={`score-${scoreColor}`}
      />
      <StatCard
        label="Lines Added"
        value={stats.today?.lines_added || 0}
        subtext="insertions"
        className="stat-positive"
      />
      <StatCard
        label="Lines Deleted"
        value={stats.today?.lines_deleted || 0}
        subtext="deletions"
        className="stat-negative"
      />
      <StatCard
        label="This Week"
        value={stats.this_week?.total_commits || 0}
        subtext="commits"
      />
      <StatCard
        label="Files Changed"
        value={stats.today?.files_touched || 0}
        subtext="today"
      />
    </div>
  );
}

function StatCard({ label, value, subtext, className = '' }) {
  return (
    <div className={`stat-card ${className}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {subtext && <div className="stat-subtext">{subtext}</div>}
    </div>
  );
}
