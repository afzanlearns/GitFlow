import React from 'react';
import './RepositoryInfo.css';

export default function RepositoryInfo({ repos, patterns }) {
  return (
    <div className="repo-section">
      <div className="repo-container">
        <h3 className="section-title">Repositories</h3>
        <table className="repo-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Branch</th>
              <th>Remote URL</th>
              <th>Commits</th>
            </tr>
          </thead>
          <tbody>
            {repos.length > 0 ? (
              repos.map((repo, i) => (
                <tr key={i}>
                  <td className="cell-repo">{repo.repository}</td>
                  <td className="cell-branch">{repo.branch || '-'}</td>
                  <td className="cell-url">
                    <code>{repo.remote_url || '-'}</code>
                  </td>
                  <td className="cell-commits">{repo.commits}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="empty">No repositories tracked</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {patterns && (
        <div className="patterns-container">
          <h3 className="section-title">Insights</h3>
          <div className="insights-grid">
            <InsightCard
              label="Peak Hour"
              value={patterns.peak_hour ? `${patterns.peak_hour}:00 UTC` : '-'}
            />
            <InsightCard
              label="Most Active Day"
              value={patterns.best_day || '-'}
            />
            <InsightCard
              label="Hot File"
              value={patterns.hot_files?.[0]?.path || '-'}
              isCode
            />
          </div>
        </div>
      )}
    </div>
  );
}

function InsightCard({ label, value, isCode = false }) {
  return (
    <div className="insight-card">
      <div className="insight-label">{label}</div>
      <div className={`insight-value ${isCode ? 'code' : ''}`}>{value}</div>
    </div>
  );
}
