import React from 'react';

export function MetricCard({ title, value, subtitle, icon, trend, variant = 'default' }) {
  return (
    <div className={`metric-card metric-${variant}`}>
      <div className="metric-header">
        <span className="metric-title">
          {icon && (
            typeof icon === 'string' && icon.length > 2 ? (
              <span className="material-symbols-outlined metric-icon">{icon}</span>
            ) : (
              <span className="metric-icon">{icon}</span>
            )
          )}
          {title}
        </span>
        {trend && <span className="metric-trend">{trend}</span>}
      </div>
      <div className="metric-value">{value}</div>
      {subtitle && <div className="metric-subtitle">{subtitle}</div>}
    </div>
  );
}
