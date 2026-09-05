import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { ZoneOverlay } from '../components/ZoneOverlay';
import { ZoneDrawingCanvas } from '../components/ZoneDrawingCanvas';

export function Zones({ cameras }) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || '');
  const [zones, setZones] = useState([]);
  const [editorOpen, setEditorOpen] = useState(false);
  const [frameUrl, setFrameUrl] = useState('');

  // Editor form state
  const [zoneName, setZoneName] = useState('');
  const [zoneType, setZoneType] = useState('restricted');
  const [targetCategories, setTargetCategories] = useState('all');
  const [drawnCoordinates, setDrawnCoordinates] = useState([]);
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

  // ── Open / Close Editor ──────────────────────────────────────────
  const openEditor = useCallback(() => {
    if (!selectedCameraId && cameras.length > 0) {
      setSelectedCameraId(cameras[0].camera_id);
    }
    setZoneName('');
    setZoneType('restricted');
    setTargetCategories('all');
    setError(null);
    setEditorOpen(true);
  }, [selectedCameraId, cameras]);

  const closeEditor = useCallback(() => {
    setEditorOpen(false);
    setDrawnCoordinates([]);
    setError(null);
  }, []);

  // ── Submit zone from visual editor ───────────────────────────────
  const handleSaveZone = useCallback(
    async (e) => {
      e.preventDefault();
      setError(null);

      if (!zoneName.trim()) {
        setError('Zone name is required.');
        return;
      }

      if (drawnCoordinates.length < 3) {
        setError('Draw a polygon with at least 3 vertices on the canvas.');
        return;
      }

      const coordinates = drawnCoordinates.map((p) => ({ x: p.x, y: p.y }));
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
        closeEditor();
        fetchZones();
      } catch (err) {
        setError(err.message || 'Failed to create zone');
      }
    },
    [zoneName, zoneType, targetCategories, drawnCoordinates, selectedCameraId, closeEditor, fetchZones],
  );

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

  // Snapshot URL for the drawing canvas (unannotated raw frame)
  const canvasImageUrl = selectedCameraId ? api.getFrameUrl(selectedCameraId, false) : '';

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
          <button className="btn-primary" onClick={openEditor}>
            + Define Zone
          </button>
        </div>
      </div>

      {error && !editorOpen && <div className="error-banner">{error}</div>}

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

      {/* ═══════ Visual Zone Editor Modal ═══════ */}
      {editorOpen && (
        <div className="modal-backdrop zone-editor-modal" onClick={(e) => { if (e.target === e.currentTarget) closeEditor(); }}>
          <div className="modal-content">
            {/* Modal header */}
            <div className="modal-header">
              <div>
                <h3>Define Virtual Zone — {selectedCameraId}</h3>
                <span className="modal-sub">
                  Draw polygon perimeter on the camera snapshot. Drag vertices to adjust.
                </span>
              </div>
              <button className="btn-close" onClick={closeEditor} title="Cancel">
                ✕
              </button>
            </div>

            {/* Editor layout: canvas + sidebar */}
            <div className="zone-editor-layout">
              {/* Drawing Canvas */}
              <ZoneDrawingCanvas
                cameraId={selectedCameraId}
                imageUrl={canvasImageUrl}
                zoneType={zoneType}
                onCoordinatesChange={setDrawnCoordinates}
              />

              {/* Sidebar form */}
              <div className="zone-editor-sidebar">
                <h4>Zone Configuration</h4>

                {error && <div className="error-banner">{error}</div>}

                <form onSubmit={handleSaveZone} style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1 }}>
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
                      <option value="restricted">Restricted (INTRUSION Alarm)</option>
                      <option value="monitoring">Monitoring (ENTER / EXIT)</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label>Target Entity Filter</label>
                    <input
                      type="text"
                      placeholder="all or person, vehicle"
                      value={targetCategories}
                      onChange={(e) => setTargetCategories(e.target.value)}
                    />
                  </div>

                  {/* Live coordinate list */}
                  <div className="form-group">
                    <label>Polygon Vertices ({drawnCoordinates.length})</label>
                    {drawnCoordinates.length > 0 ? (
                      <div className="zone-coord-list">
                        {drawnCoordinates.map((pt, i) => (
                          <div key={i} className="zone-coord-item">
                            <span>
                              <span className="coord-index">V{i + 1}</span>
                              <span className="coord-value">[{pt.x}, {pt.y}]</span>
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '10px',
                        color: 'var(--text-dim)',
                      }}>
                        Draw on the canvas to generate vertices
                      </span>
                    )}
                  </div>

                  <div className="form-actions">
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={drawnCoordinates.length < 3}
                      style={{ opacity: drawnCoordinates.length < 3 ? 0.5 : 1 }}
                    >
                      Save &amp; Arm Virtual Zone
                    </button>
                    <button type="button" className="btn-secondary" onClick={closeEditor}>
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
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
