import React, { useState } from 'react';
import { useTracking } from '../hooks/useTracking';

export function Cameras({ cameras, healthMap, onStart, onStop, onDelete, onCreate }) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || '');
  const [formOpen, setFormOpen] = useState(false);
  const [formData, setFormData] = useState({
    camera_id: '',
    name: '',
    location: '',
    source_type: 'file',
    source_url: './media/sample/test.mp4',
    target_fps: 5,
    buffer_size: 10,
    enabled: true,
  });
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { tracks, detections } = useTracking(selectedCameraId, 2000);

  const onlineCount = cameras.filter((c) => healthMap[c.camera_id]?.status === 'ONLINE').length;
  const standbyCount = cameras.length - onlineCount;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      await onCreate({
        ...formData,
        target_fps: parseInt(formData.target_fps, 10),
        buffer_size: parseInt(formData.buffer_size, 10),
      });
      setFormOpen(false);
      setFormData({
        camera_id: '',
        name: '',
        location: '',
        source_type: 'file',
        source_url: './media/sample/test.mp4',
        target_fps: 5,
        buffer_size: 10,
        enabled: true,
      });
    } catch (err) {
      setFormError(err.message || 'Failed to add camera');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Camera Streams &amp; Edge Ingestion</h1>
          <p className="page-subtitle">Configure IP CCTV, RTSP, and optical surveillance streams with neural hooks</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="system-pill">
            <span className="status-indicator status-up" />
            <span>{onlineCount} Online</span>
            <span style={{ color: 'var(--text-dim)' }}>|</span>
            <span style={{ color: 'var(--solar-amber)' }}>{standbyCount} Standby</span>
          </div>
          <button className="btn-primary" onClick={() => setFormOpen(!formOpen)}>
            {formOpen ? 'Cancel' : '+ Register Stream'}
          </button>
        </div>
      </div>

      {/* Add Camera Form Collapsible */}
      {formOpen && (
        <div className="card form-card">
          <h3>Register New Video Stream</h3>
          {formError && <div className="error-banner">{formError}</div>}
          <form onSubmit={handleSubmit} className="form-grid">
            <div className="form-group">
              <label>Camera Designation ID</label>
              <input
                type="text"
                required
                placeholder="e.g. CAM-NORTH-01"
                value={formData.camera_id}
                onChange={(e) => setFormData({ ...formData, camera_id: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Stream Designation Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Perimeter Gate Optical"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Physical Installation Sector</label>
              <input
                type="text"
                required
                placeholder="e.g. Sector 4 North Fence"
                value={formData.location}
                onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Source Type</label>
              <select
                value={formData.source_type}
                onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
              >
                <option value="file">Video File (MP4/MKV)</option>
                <option value="rtsp">RTSP IP Stream</option>
                <option value="webcam">USB / Direct Webcam (0)</option>
              </select>
            </div>

            <div className="form-group full-width">
              <label>Source URL / Device Path</label>
              <input
                type="text"
                required
                placeholder="rtsp://admin:pass@192.168.1.100:554/h264 or 0 or ./media/sample/test.mp4"
                value={formData.source_url}
                onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Sampling FPS Rate</label>
              <input
                type="number"
                min="1"
                max="60"
                value={formData.target_fps}
                onChange={(e) => setFormData({ ...formData, target_fps: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label>Buffer Window Size</label>
              <input
                type="number"
                min="1"
                max="100"
                value={formData.buffer_size}
                onChange={(e) => setFormData({ ...formData, buffer_size: e.target.value })}
              />
            </div>

            <div className="form-group full-width form-actions" style={{ marginTop: '8px' }}>
              <button type="submit" className="btn-primary" disabled={isSubmitting}>
                {isSubmitting ? 'Registering Stream...' : 'Initialize & Connect Stream'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Camera Inventory Table */}
      <div className="card table-card">
        <h3 style={{ padding: '14px 18px 0 18px', border: 'none', margin: 0 }}>Stream Inventory &amp; Telemetry</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name &amp; Location</th>
              <th>Status</th>
              <th>FPS (Cur / Target)</th>
              <th>Resolution</th>
              <th>Uptime</th>
              <th>Commands</th>
            </tr>
          </thead>
          <tbody>
            {cameras.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
                  No camera streams registered in mission control database.
                </td>
              </tr>
            ) : (
              cameras.map((cam) => {
                const health = healthMap[cam.camera_id];
                const status = health?.status || (cam.enabled ? 'CONNECTING' : 'STOPPED');
                const isOnline = status === 'ONLINE';

                return (
                  <tr
                    key={cam.camera_id}
                    className={selectedCameraId === cam.camera_id ? 'row-selected' : ''}
                    onClick={() => setSelectedCameraId(cam.camera_id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td><strong>{cam.camera_id}</strong></td>
                    <td>
                      <div>{cam.name}</div>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{cam.location}</span>
                    </td>
                    <td>
                      <span className={`status-pill status-${status}`}>
                        {status ? status.charAt(0).toUpperCase() + status.slice(1).toLowerCase() : ''}
                      </span>
                    </td>
                    <td>{(health?.current_fps ?? 0).toFixed ? (health?.current_fps ?? 0).toFixed(1) : health?.current_fps} / {cam.target_fps}</td>
                    <td>{health?.resolution || '--'}</td>
                    <td>{health?.uptime_seconds ? `${health.uptime_seconds}s` : '--'}</td>
                    <td onClick={(e) => e.stopPropagation()}>
                      {isOnline ? (
                        <button className="btn-small btn-danger" onClick={() => onStop(cam.camera_id)}>
                          Stop
                        </button>
                      ) : (
                        <button className="btn-small btn-success" onClick={() => onStart(cam.camera_id)}>
                          Start
                        </button>
                      )}
                      <button
                        className="btn-small btn-secondary"
                        onClick={() => {
                          if (confirm(`De-register camera stream ${cam.camera_id}?`)) {
                            onDelete(cam.camera_id);
                          }
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Selected Camera Analytics Inspector */}
      {selectedCameraId && (
        <div className="inspector-grid">
          <div className="card">
            <h3>Active Object Tracks ({selectedCameraId})</h3>
            {tracks.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px', padding: '12px 0' }}>
                No active tracking vectors detected on sensor {selectedCameraId}.
              </p>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Track ID</th>
                    <th>Classification</th>
                    <th>Confidence</th>
                    <th>Vector [X, Y]</th>
                    <th>Age</th>
                  </tr>
                </thead>
                <tbody>
                  {tracks.map((t) => (
                    <tr key={t.track_id}>
                      <td><strong>#{t.track_id}</strong></td>
                      <td><span className="badge-class">{t.class_name}</span></td>
                      <td>{(t.confidence * 100).toFixed(1)}%</td>
                      <td>[{Math.round(t.current_position.x)}, {Math.round(t.current_position.y)}]</td>
                      <td>{t.track_age}f</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          <div className="card">
            <h3>Neural Detections ({selectedCameraId})</h3>
            {detections.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px', padding: '12px 0' }}>
                No bounding box classifications detected on sensor {selectedCameraId}.
              </p>
            ) : (
              <div className="detection-list">
                {detections.slice(0, 8).map((d, idx) => (
                  <div key={idx} className="detection-item">
                    <span className="badge-class">{d.class_name}</span>
                    <span style={{ color: '#ffffff' }}>{(d.confidence * 100).toFixed(1)}%</span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '10px' }}>
                      {d.timestamp ? new Date(d.timestamp).toLocaleTimeString() : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
