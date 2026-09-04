import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function Zones({ cameras }) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || '');
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  // New zone form state
  const [zoneName, setZoneName] = useState('');
  const [zoneType, setZoneType] = useState('restricted');
  const [coordsInput, setCoordsInput] = useState('100,100; 500,100; 500,400; 100,400');
  const [targetCategories, setTargetCategories] = useState('all');
  const [error, setError] = useState(null);

  const fetchZones = useCallback(async () => {
    if (!selectedCameraId) return;
    setLoading(true);
    try {
      const res = await api.getZones(selectedCameraId);
      setZones(res.zones || []);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch zones');
    } finally {
      setLoading(false);
    }
  }, [selectedCameraId]);

  useEffect(() => {
    if (cameras.length > 0 && !selectedCameraId) {
      setSelectedCameraId(cameras[0].camera_id);
    }
  }, [cameras, selectedCameraId]);

  useEffect(() => {
    fetchZones();
  }, [fetchZones]);

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
          <h1>Virtual Fences & Zones</h1>
          <p className="page-subtitle">Define polygon boundaries for intrusion and movement detection</p>
        </div>

        <div className="header-actions">
          <select
            className="select-camera"
            value={selectedCameraId}
            onChange={(e) => setSelectedCameraId(e.target.value)}
          >
            {cameras.map((c) => (
              <option key={c.camera_id} value={c.camera_id}>
                {c.name} ({c.camera_id})
              </option>
            ))}
          </select>
          <button className="btn-primary" onClick={() => setFormOpen(!formOpen)}>
            {formOpen ? 'Cancel' : '+ New Zone'}
          </button>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Add Zone Form */}
      {formOpen && (
        <div className="card form-card">
          <h3>Create Virtual Polygon Zone</h3>
          <form onSubmit={handleCreateZone} className="form-grid">
            <div className="form-group">
              <label>Zone Name</label>
              <input
                type="text"
                required
                placeholder="e.g. Restricted Perimeter"
                value={zoneName}
                onChange={(e) => setZoneName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Zone Security Type</label>
              <select value={zoneType} onChange={(e) => setZoneType(e.target.value)}>
                <option value="restricted">Restricted (Triggers INTRUSION alert)</option>
                <option value="monitoring">Monitoring (Triggers ENTER / EXIT only)</option>
              </select>
            </div>

            <div className="form-group full-width">
              <label>Polygon Vertices (X,Y separated by semicolons)</label>
              <input
                type="text"
                required
                placeholder="100,100; 500,100; 500,400; 100,400"
                value={coordsInput}
                onChange={(e) => setCoordsInput(e.target.value)}
              />
              <small className="help-text">Minimum 3 coordinates. Coordinates map to camera pixel resolution.</small>
            </div>

            <div className="form-group full-width">
              <label>Target Categories (comma-separated)</label>
              <input
                type="text"
                placeholder="all or person, vehicle"
                value={targetCategories}
                onChange={(e) => setTargetCategories(e.target.value)}
              />
            </div>

            <div className="form-group full-width form-actions">
              <button type="submit" className="btn-primary">Save Virtual Zone</button>
            </div>
          </form>
        </div>
      )}

      {/* Zone List Cards */}
      <div className="zone-grid">
        {zones.length === 0 ? (
          <div className="card empty-card full-width">
            <span className="empty-icon">📐</span>
            <h3>No Virtual Zones Defined</h3>
            <p>Define virtual fences to start generating security intrusion alerts for {selectedCameraId}.</p>
          </div>
        ) : (
          zones.map((zone) => {
            const isRestricted = zone.zone_type === 'restricted';

            return (
              <div key={zone.zone_id} className={`card zone-card ${isRestricted ? 'zone-restricted' : 'zone-monitoring'}`}>
                <div className="zone-header">
                  <div>
                    <h4>{zone.name}</h4>
                    <span className="zone-id">ID: {zone.zone_id}</span>
                  </div>
                  <span className={`badge-zone ${isRestricted ? 'badge-danger' : 'badge-info'}`}>
                    {zone.zone_type.toUpperCase()}
                  </span>
                </div>

                <div className="zone-body">
                  <div className="zone-row">
                    <span className="label">Target Filter:</span>
                    <span className="val">
                      {zone.target_categories?.map((cat, i) => (
                        <span key={i} className="badge-class">{cat}</span>
                      ))}
                    </span>
                  </div>

                  <div className="zone-row">
                    <span className="label">Vertices ({zone.coordinates?.length || 0}):</span>
                    <div className="coords-box">
                      {zone.coordinates?.map((pt, i) => (
                        <span key={i} className="coord-chip">({Math.round(pt.x)}, {Math.round(pt.y)})</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="zone-footer">
                  <button className="btn-small btn-danger" onClick={() => handleDeleteZone(zone.zone_id)}>
                    Delete
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
