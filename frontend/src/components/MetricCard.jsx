import React from 'react';

export function MetricCard({ title, value, subtitle, icon, trend, variant = 'default' }) {
  return (
    <div className={`metric-card metric-${variant}`}>
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {icon && <span className="metric-icon">{icon}</span>}
      </div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
    </div>
  );
}
