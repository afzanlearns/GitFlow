import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import './Charts.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function Charts({ stats, history }) {
  const isDark = document.documentElement.classList.contains('dark-mode');
  const textColor = isDark ? '#ffffff' : '#0a0a0a';
  const gridColor = isDark ? '#333333' : '#e5e5e5';

  const commitChartData = {
    labels: history.map(h => h.date),
    datasets: [
      {
        label: 'Commits',
        data: history.map(h => h.commits || 0),
        borderColor: '#0070f3',
        backgroundColor: 'rgba(0, 112, 243, 0.05)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: '#0070f3',
        pointBorderColor: textColor,
        pointBorderWidth: 2,
      },
    ],
  };

  const scoreChartData = {
    labels: history.map(h => h.date),
    datasets: [
      {
        label: 'Score',
        data: history.map(h => h.score || 0),
        borderColor: '#0cce6b',
        backgroundColor: 'rgba(12, 206, 107, 0.05)',
        fill: true,
        tension: 0.4,
        pointRadius: 3,
        pointBackgroundColor: '#0cce6b',
        pointBorderColor: textColor,
        pointBorderWidth: 2,
      },
    ],
  };

  const repoChartData = {
    labels: (stats?.repositories || []).map(r => r.repository),
    datasets: [
      {
        label: 'Commits',
        data: (stats?.repositories || []).map(r => r.commits),
        backgroundColor: '#0070f3',
      },
      {
        label: 'Lines Added',
        data: (stats?.repositories || []).map(r => r.lines_added),
        backgroundColor: '#0cce6b',
      },
    ],
  };

  const commonOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: true,
        labels: {
          color: textColor,
          font: { size: 12, family: 'system-ui, -apple-system' },
          padding: 16,
          usePointStyle: true,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: '#fff',
        bodyColor: '#fff',
        borderColor: gridColor,
        borderWidth: 1,
        padding: 12,
        displayColors: true,
      },
    },
    scales: {
      x: {
        grid: { color: gridColor, drawBorder: false },
        ticks: { color: textColor, font: { size: 12 } },
      },
      y: {
        grid: { color: gridColor, drawBorder: false },
        ticks: { color: textColor, font: { size: 12 } },
        beginAtZero: true,
      },
    },
  };

  return (
    <div className="charts-section">
      <div className="chart-container">
        <h3 className="chart-title">Commit Trend</h3>
        <Line data={commitChartData} options={commonOptions} height={80} />
      </div>

      <div className="chart-container">
        <h3 className="chart-title">Productivity Score</h3>
        <Line data={scoreChartData} options={commonOptions} height={80} />
      </div>

      <div className="chart-container full-width">
        <h3 className="chart-title">Repository Breakdown</h3>
        <Bar
          data={repoChartData}
          options={commonOptions}
          height={80}
        />
      </div>
    </div>
  );
}
