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
            <span className="brand-title">VICENTRA</span>
            <span className="brand-tag">IBVAP CORE</span>
          </div>
        </div>

        <nav className="navbar-links">
          <NavLink to="/" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="material-symbols-outlined nav-icon">dashboard</span>
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/cameras" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="material-symbols-outlined nav-icon">videocam</span>
            <span>Cameras</span>
          </NavLink>
          <NavLink to="/zones" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="material-symbols-outlined nav-icon">crop_free</span>
            <span>Virtual Zones</span>
          </NavLink>
          <NavLink to="/events" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="material-symbols-outlined nav-icon">history_toggle_off</span>
            <span>Incident Log</span>
          </NavLink>
        </nav>
      </div>

      <div className="navbar-right">
        <div className="system-pill" title="Backend Stream Manager Telemetry">
          <span className={`status-indicator ${isServerUp ? 'status-up' : 'status-down'}`} />
          <span className="system-pill-status">SYSTEM {isServerUp ? 'ONLINE' : 'OFFLINE'}</span>
          <span className="stream-count-divider">|</span>
          <span className="stream-count">{activeStreams}/{totalStreams} STREAMS</span>
        </div>

        <ConnectionBadge status={wsStatus} />
      </div>
    </header>
  );
}
