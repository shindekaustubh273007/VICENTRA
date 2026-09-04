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

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Security Incident Log</h1>
          <p className="page-subtitle">Historical audit trail of all virtual fence crossings and intrusion events</p>
        </div>

        <button className="btn-secondary" onClick={fetchEvents} disabled={loading}>
          {loading ? 'Refreshing...' : '🔄 Refresh Log'}
        </button>
      </div>

      {/* Filter Bar */}
      <div className="card filter-card">
        <div className="filter-group">
          <label>Camera</label>
          <select value={filterCamera} onChange={(e) => setFilterCamera(e.target.value)}>
            <option value="">All Cameras</option>
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                {c.name} ({c.camera_id})
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>Event Type</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="">All Events</option>
            <option value="INTRUSION">🚨 INTRUSION (Restricted)</option>
            <option value="ENTER">➡️ ENTER (Monitoring)</option>
            <option value="EXIT">⬅️ EXIT</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Limit</label>
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
              <th>Timestamp</th>
              <th>Type</th>
              <th>Camera</th>
              <th>Zone Name</th>
              <th>Object Class</th>
              <th>Track ID</th>
              <th>Ground Coordinates</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan="7" className="empty-cell">
                  {loading ? 'Loading security events...' : 'No security events found matching criteria.'}
                </td>
              </tr>
            ) : (
              events.map((evt) => {
                const isIntrusion = evt.event_type === 'INTRUSION';
                const isEnter = evt.event_type === 'ENTER';

                const badgeClass = isIntrusion
                  ? 'badge-danger'
                  : isEnter
                  ? 'badge-warning'
                  : 'badge-secondary';

                return (
                  <tr key={evt.event_id || `${evt.camera_id}_${evt.timestamp}`}>
                    <td>{formatTimestamp(evt.timestamp)}</td>
                    <td>
                      <span className={`status-pill ${badgeClass}`}>
                        {evt.event_type}
                      </span>
                    </td>
                    <td><strong>{evt.camera_id}</strong></td>
                    <td>{evt.zone_name || evt.zone_id}</td>
                    <td><span className="badge-class">{evt.object_class}</span></td>
                    <td>#{evt.track_id}</td>
                    <td>
                      {evt.position
                        ? `(${Math.round(evt.position.x)}, ${Math.round(evt.position.y)})`
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
