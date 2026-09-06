import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function Events({ cameras }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  // Filters
  const [filterCamera, setFilterCamera] = useState('');
  const [filterType, setFilterType] = useState('');
  const [limit, setLimit] = useState(50);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getEvents({
        cameraId: filterCamera || undefined,
        eventType: filterType || undefined,
        limit,
      });
      setEvents(res.events || []);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  }, [filterCamera, filterType, limit]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const formatTimestamp = (ts) => {
    if (!ts) return '--';
    const date = new Date(ts);
    return date.toLocaleString();
  };

  const handleClearAudit = async () => {
    const scopeMsg = filterCamera
      ? `Acknowledge and purge all security incident records for sensor ${filterCamera}?`
      : 'Acknowledge and purge ALL security incident records from the audit log?';
    if (window.confirm(scopeMsg)) {
      try {
        setLoading(true);
        await api.clearEvents({
          cameraId: filterCamera || undefined,
        });
        setEvents([]);
      } catch (err) {
        console.error('Failed to clear audit log:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Security Incident Audit Log</h1>
          <p className="page-subtitle">Chronological tamper-evident audit record of perimeter fence crossings and intrusion events</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button className="btn-secondary" onClick={fetchEvents} disabled={loading} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <span className="material-symbols-outlined text-sm">sync</span>
            <span>{loading ? 'Querying...' : 'Refresh Audit'}</span>
          </button>
          <button
            className="btn-danger"
            onClick={handleClearAudit}
            disabled={loading || events.length === 0}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            title="Acknowledge and clear audit log"
          >
            <span className="material-symbols-outlined text-sm">delete_sweep</span>
            <span>Clear Audit</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card filter-card">
        <div className="filter-group">
          <label>Surveillance Sensor</label>
          <select value={filterCamera} onChange={(e) => setFilterCamera(e.target.value)}>
            <option value="">All Sensors</option>
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                {c.name} ({c.camera_id})
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Event Category</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="">All Incidents</option>
            <option value="INTRUSION">Critical intrusion (Restricted)</option>
            <option value="ENTER">Zone entry (Monitoring)</option>
            <option value="EXIT">Zone exit (Boundary exit)</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Record Depth</label>
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            <option value="25">25 records</option>
            <option value="50">50 records</option>
            <option value="100">100 records</option>
          </select>
        </div>
      </div>

      {/* Events Table */}
      <div className="card table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp (UTC / Local)</th>
              <th>Incident Type</th>
              <th>Sensor ID</th>
              <th>Virtual Zone</th>
              <th>Classification</th>
              <th>Track Vector</th>
              <th>Ground Coordinates</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  {loading ? 'Querying incident audit database...' : 'No security incidents found matching current filter parameters.'}
                </td>
              </tr>
            ) : (
              events.map((evt) => {
                const isIntrusion = evt.event_type === 'INTRUSION';
                const isEnter = evt.event_type === 'ENTER';

                const badgeClass = isIntrusion
                  ? 'status-ERROR'
                  : isEnter
                  ? 'status-CONNECTING'
                  : 'status-OFFLINE';

                return (
                  <tr key={evt.event_id || `${evt.camera_id}_${evt.timestamp}`}>
                    <td style={{ color: 'var(--text-muted)', fontSize: '11px' }}>{formatTimestamp(evt.timestamp)}</td>
                    <td>
                      <span className={`status-pill ${badgeClass}`}>
                        {evt.event_type ? evt.event_type.charAt(0).toUpperCase() + evt.event_type.slice(1).toLowerCase() : ''}
                      </span>
                    </td>
                    <td><strong>{evt.camera_id}</strong></td>
                    <td style={{ color: '#ffffff' }}>{evt.zone_name || evt.zone_id}</td>
                    <td><span className="badge-class">{evt.object_class || 'entity'}</span></td>
                    <td>#{evt.track_id}</td>
                    <td style={{ color: 'var(--text-dim)' }}>
                      {evt.position
                        ? `[${Math.round(evt.position.x)}, ${Math.round(evt.position.y)}]`
                        : '--'}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
