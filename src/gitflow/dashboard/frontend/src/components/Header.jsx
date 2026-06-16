import React from 'react';
import './Header.css';

export default function Header({ darkMode, onToggleDarkMode, onRefresh }) {
  return (
    <header className="header">
      <div className="header-left">
        <h1 className="logo">GitFlow</h1>
        <p className="tagline">Git Analytics</p>
      </div>

      <div className="header-right">
        <button className="btn-refresh" onClick={onRefresh} title="Refresh data">
          Refresh
        </button>

        <button
          className="btn-theme"
          onClick={onToggleDarkMode}
          title={darkMode ? 'Light mode' : 'Dark mode'}
          aria-label="Toggle theme"
        >
          {darkMode ? '\u2600' : '\u263E'}
        </button>

        <a href="/docs" className="btn-docs" target="_blank" rel="noopener noreferrer">
          API Docs
        </a>
      </div>
    </header>
  );
}
