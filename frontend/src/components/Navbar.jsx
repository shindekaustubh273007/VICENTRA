import React from 'react';
import { NavLink } from 'react-router-dom';
import { ConnectionBadge } from './ConnectionBadge';

export function Navbar({ wsStatus, globalHealth }) {
  const isServerUp = globalHealth?.status === 'UP';
  const activeStreams = globalHealth?.active_streams ?? 0;
  const totalStreams = globalHealth?.total_managed ?? 0;

  return (
    <header className="navbar">
      <div className="navbar-left">
        <div className="navbar-brand">
          <div className="brand-icon-box">
            <span className="material-symbols-outlined">shield</span>
          </div>
          <div className="brand-text">
            <span className="brand-title">Vicentra</span>
            <span className="brand-tag">Ibvap Core</span>
          </div>
        </div>

        <nav className="navbar-links">
          <NavLink to="/" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Dashboard
          </NavLink>
          <NavLink to="/cameras" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Cameras
          </NavLink>
          <NavLink to="/zones" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Virtual Zones
          </NavLink>
          <NavLink to="/events" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            Incident Log
          </NavLink>
        </nav>
      </div>

      <div className="navbar-right">
        <div className="system-pill" title="Backend Server Status">
          <span className={`status-indicator ${isServerUp ? 'status-up' : 'status-down'}`} />
          <span>System: {isServerUp ? 'Online' : 'Offline'}</span>
          <span className="stream-count">({activeStreams}/{totalStreams} streams)</span>
        </div>

        <ConnectionBadge status={wsStatus} />
      </div>
    </header>
  );
}
