import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ZoneOverlay } from '../components/ZoneOverlay';

export function Zones({ cameras }) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || '');
  const [zones, setZones] = useState([]);
  const [formOpen, setFormOpen] = useState(false);
  const [frameUrl, setFrameUrl] = useState('');

  // New zone form state
  const [zoneName, setZoneName] = useState('');
  const [zoneType, setZoneType] = useState('restricted');
  const [coordsInput, setCoordsInput] = useState('100,100; 500,100; 500,400; 100,400');
  const [targetCategories, setTargetCategories] = useState('all');
  const [error, setError] = useState(null);

  const fetchZones = useCallback(async () => {
    if (!selectedCameraId) return;
    try {
      const res = await api.getZones(selectedCameraId);
      setZones(res.zones || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch zones');
    }
  }, [selectedCameraId]);

  useEffect(() => {
    if (cameras.length > 0 && !selectedCameraId) {
      setSelectedCameraId(cameras[0].camera_id);
    }
  }, [cameras, selectedCameraId]);

  useEffect(() => {
    fetchZones();
    if (selectedCameraId) {
      setFrameUrl(api.getFrameUrl(selectedCameraId, false));
    }
  }, [fetchZones, selectedCameraId]);

  const handleCreateZone = async (e) => {
    e.preventDefault();
    setError(null);

    // Parse coordinates from string format: "x1,y1; x2,y2; ..."
    const rawPoints = coordsInput
      .split(';')
      .map((p) => p.trim())
      .filter(Boolean);

    if (rawPoints.length < 3) {
      setError('A polygon zone must have at least 3 vertices (separated by semicolons).');
      return;
    }

    const coordinates = [];
    for (const pt of rawPoints) {
      const [xStr, yStr] = pt.split(',').map((s) => s.trim());
      const x = parseFloat(xStr);
      const y = parseFloat(yStr);
      if (isNaN(x) || isNaN(y)) {
        setError(`Invalid coordinate point: "${pt}". Use format "X,Y" e.g. "100,200".`);
        return;
      }
      coordinates.push({ x, y });
    }

    const categories = targetCategories
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean);

    try {
      await api.createZone(selectedCameraId, {
        name: zoneName,
        zone_type: zoneType,
        coordinates,
        target_categories: categories.length ? categories : ['all'],
        enabled: true,
      });
      setFormOpen(false);
      setZoneName('');
      fetchZones();
    } catch (err) {
      setError(err.message || 'Failed to create zone');
    }
  };

  const handleDeleteZone = async (zoneId) => {
    if (confirm(`Delete zone ${zoneId}?`)) {
      try {
        await api.deleteZone(zoneId);
        fetchZones();
      } catch (err) {
        setError(err.message || 'Failed to delete zone');
      }
    }
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1>Virtual Fences &amp; Boundary Calibration</h1>
          <p className="page-subtitle">Configure polygon perimeter tripwires and restricted intrusion zones</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select
            value={selectedCameraId}
            onChange={(e) => setSelectedCameraId(e.target.value)}
            style={{ padding: '7px 12px' }}
          >
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                {c.name} ({c.camera_id})
              </option>
            ))}
          </select>
          <button className="btn-primary" onClick={() => setFormOpen(!formOpen)}>
            {formOpen ? 'Cancel' : '+ Define Zone'}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Hero Spatial Viewport with Live SVG Zone Overlay */}
      <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '10px 16px',
          background: 'rgba(10, 10, 13, 0.95)',
          borderBottom: '1px solid var(--hairline-divider)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontFamily: 'var(--font-mono)', fontSize: '11px' }}>
            <span className="material-symbols-outlined text-sm" style={{ color: 'var(--status-cyan)' }}>polyline</span>
            <span style={{ color: '#ffffff', fontWeight: '700' }}>Spatial fence mesh</span>
            <span style={{ color: 'var(--text-dim)' }}>|</span>
            <span style={{ color: 'var(--text-muted)' }}>Sensor: {selectedCameraId || 'None'}</span>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-muted)' }}>
            {zones.length} {zones.length === 1 ? 'zone active' : 'zones active'}
          </div>
        </div>

        <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', backgroundColor: '#000000', overflow: 'hidden' }}>
          {selectedCameraId ? (
            <img
              src={frameUrl}
              alt="Camera Zone Viewport"
              style={{ width: '100%', height: '100%', objectFit: 'contain' }}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          ) : null}
          <ZoneOverlay zones={zones} width={1280} height={720} />
        </div>
      </div>

      {/* Add Zone Form */}
      {formOpen && (
        <div className="card form-card">
          <h3>Create Virtual Polygon Perimeter</h3>
          <form onSubmit={handleCreateZone} className="form-grid">
            <div className="form-group">
              <label>Zone Designation Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Restricted North Gate"
                value={zoneName}
                onChange={(e) => setZoneName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Security Level</label>
              <select value={zoneType} onChange={(e) => setZoneType(e.target.value)}>
                <option value="restricted">Restricted (Triggers Immediate INTRUSION Alarm)</option>
                <option value="monitoring">Monitoring (Telemetry ENTER / EXIT Only)</option>
              </select>
            </div>

            <div className="form-group full-width">
              <label>Polygon Vertex Coordinates (X,Y separated by semicolons)</label>
              <input
                type="text"
                required
                placeholder="100,100; 500,100; 500,400; 100,400"
                value={coordsInput}
                onChange={(e) => setCoordsInput(e.target.value)}
              />
              <small className="help-text">Minimum 3 vertices required. Coordinates map to camera pixel grid (e.g. 1280x720).</small>
            </div>

            <div className="form-group full-width">
              <label>Target Entity Filter (comma-separated)</label>
              <input
                type="text"
                placeholder="all or person, vehicle, bicycle"
                value={targetCategories}
                onChange={(e) => setTargetCategories(e.target.value)}
              />
            </div>

            <div className="form-group full-width form-actions" style={{ marginTop: '6px' }}>
              <button type="submit" className="btn-primary">Save &amp; Arm Virtual Zone</button>
            </div>
          </form>
        </div>
      )}

      {/* Zone Registry Grid */}
      <div>
        <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', fontWeight: '700', color: '#ffffff', marginBottom: '12px', letterSpacing: '0.5px' }}>
          Configured Virtual Zones ({selectedCameraId})
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '14px' }}>
          {zones.length === 0 ? (
            <div className="card" style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '36px', color: 'var(--text-muted)' }}>
              <span className="material-symbols-outlined" style={{ fontSize: '32px', marginBottom: '8px', display: 'inline-block' }}>crop_free</span>
              <p style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>No virtual zones defined for {selectedCameraId || 'camera'}.</p>
            </div>
          ) : (
            zones.map((zone) => {
              const isRestricted = zone.zone_type === 'restricted';

              return (
                <div key={zone.zone_id} className="card" style={{ borderLeft: `3px solid ${isRestricted ? 'var(--neon-crimson)' : 'var(--status-cyan)'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                    <div>
                      <h4 style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: '700', color: '#ffffff' }}>{zone.name}</h4>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', color: 'var(--text-dim)' }}>ID: {zone.zone_id}</span>
                    </div>
                    <span className={`status-pill ${isRestricted ? 'status-ERROR' : 'status-ONLINE'}`}>
                      {zone.zone_type ? zone.zone_type.charAt(0).toUpperCase() + zone.zone_type.slice(1).toLowerCase() : ''}
                    </span>
                  </div>

                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    <div>
                      <span>Targets: </span>
                      {zone.target_categories?.map((cat, i) => (
                        <span key={i} className="badge-class">{cat}</span>
                      ))}
                    </div>
                    <div>
                      <span>Vertices ({zone.coordinates?.length || 0}): </span>
                      <div className="coords-box">
                        {zone.coordinates?.map((pt, i) => (
                          <span key={i} className="coord-chip">[{Math.round(pt.x)}, {Math.round(pt.y)}]</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div style={{ marginTop: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', justifyContent: 'flex-end' }}>
                    <button className="btn-small btn-danger" onClick={() => handleDeleteZone(zone.zone_id)}>
                      De-register Zone
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
