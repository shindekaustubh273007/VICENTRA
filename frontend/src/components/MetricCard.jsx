import React from 'react';

export function MetricCard({ title, value, subtitle, icon, trend, variant = 'default' }) {
  return (
    <div className={`metric-card metric-${variant}`}>
      <div className="metric-header">
        <div className="metric-title">
          {icon && (
            <div className="metric-icon-box">
              <span className="material-symbols-outlined metric-icon">{icon}</span>
            </div>
          )}
          <span className="metric-title-text">{title}</span>
        </div>
        {trend && <span className="metric-trend">{trend}</span>}
      </div>
      <div className="metric-value-row">
        <div className="metric-value">{value}</div>
      </div>
      {subtitle && (
        <div className="metric-subtitle">
          <span>{subtitle}</span>
          <span className="metric-status-dot" />
        </div>
      )}
    </div>
  );
}
