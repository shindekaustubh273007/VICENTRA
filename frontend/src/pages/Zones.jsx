import React, { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';
import { ZoneOverlay } from '../components/ZoneOverlay';
import { ZoneDrawingCanvas } from '../components/ZoneDrawingCanvas';

export function Zones({ cameras, healthMap = {} }) {
  const [selectedCameraId, setSelectedCameraId] = useState(cameras[0]?.camera_id || '');
  const [zones, setZones] = useState([]);
  const [editorOpen, setEditorOpen] = useState(false);
  const [frameUrl, setFrameUrl] = useState('');
  const [frameDims, setFrameDims] = useState({ width: 1280, height: 720 });
  const previewImgRef = useRef(null);

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

  // Periodic frame refresh for the spatial fence mesh preview
  useEffect(() => {
    if (!selectedCameraId) return;
    const health = healthMap[selectedCameraId];
    const isOnline = health?.status === 'ONLINE';
    if (!isOnline) return;

    const interval = setInterval(() => {
      setFrameUrl(api.getFrameUrl(selectedCameraId, false));
    }, 1500);
    return () => clearInterval(interval);
  }, [selectedCameraId, healthMap]);

  // Detect native frame dimensions from loaded image
  const handlePreviewImageLoad = useCallback((e) => {
    const img = e.target;
    if (img.naturalWidth > 0 && img.naturalHeight > 0) {
      setFrameDims({ width: img.naturalWidth, height: img.naturalHeight });
    }
  }, []);

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

        <div className="page-header-actions">
          <div className="select-wrapper">
            <span className="select-label">SENSOR:</span>
            <select
              value={selectedCameraId}
              onChange={(e) => setSelectedCameraId(e.target.value)}
              className="tactical-select"
            >
              {cameras.map((c) => (
                <option key={c.camera_id} value={c.camera_id}>
                  {c.name} ({c.camera_id})
                </option>
              ))}
            </select>
          </div>
          <button className="btn-primary" onClick={openEditor}>
            <span className="material-symbols-outlined text-sm">polyline</span>
            <span>+ Define Zone</span>
          </button>
        </div>
      </div>

      {error && !editorOpen && <div className="error-banner">{error}</div>}

      {/* Main 2-Column Layout: Left = Hero Spatial Viewport, Right = Configured Zones */}
      <div className="zones-workspace-grid">
        {/* Left Column: Hero Spatial Viewport */}
        <div className="zones-viewport-card">
          <div className="zones-viewport-header">
            <div className="viewport-header-left">
              <span className="material-symbols-outlined text-sm text-cyan">polyline</span>
              <span className="viewport-header-title">Spatial Fence Mesh</span>
              <span className="viewport-header-divider">|</span>
              <span className="viewport-header-sensor">Sensor: {selectedCameraId || 'None'}</span>
            </div>
            <div className="viewport-header-right">
              <span className="zones-count-pill">
                <span className="status-dot-active" />
                {zones.length} {zones.length === 1 ? 'Zone Active' : 'Zones Active'}
              </span>
            </div>
          </div>

          <div className="zones-viewport-frame hud-grid-bg">
            {selectedCameraId ? (
              <img
                ref={previewImgRef}
                src={frameUrl}
                alt="Camera Zone Viewport"
                className="zones-preview-img"
                onLoad={handlePreviewImageLoad}
                onError={(e) => {
                  e.target.style.display = 'none';
                }}
              />
            ) : null}
            <ZoneOverlay zones={zones} width={frameDims.width} height={frameDims.height} />
            <div className="zones-viewport-corner corner-tl" />
            <div className="zones-viewport-corner corner-tr" />
            <div className="zones-viewport-corner corner-bl" />
            <div className="zones-viewport-corner corner-br" />
          </div>

          <div className="zones-viewport-footer">
            <div className="viewport-footer-left">
              <span className="status-indicator status-up" />
              <span>DETECTION ACTIVE (PERSON &amp; VEHICLE)</span>
              <span className="footer-divider">•</span>
              <span className="text-muted">VIRTUAL FENCE WIREFRAME v4.2</span>
            </div>
            <div className="viewport-footer-right">
              <span>NATIVE: {frameDims.width}×{frameDims.height}</span>
            </div>
          </div>
        </div>

        {/* Right Column: Configured Zones Sidebar */}
        <div className="zones-sidebar-panel">
          <div className="zones-sidebar-header">
            <div className="sidebar-title-row">
              <span className="material-symbols-outlined text-sm text-muted">view_in_ar</span>
              <span className="sidebar-title">CONFIGURED ZONES</span>
              <span className="sidebar-count-badge">{zones.length}</span>
            </div>
            <button className="btn-small btn-secondary" onClick={openEditor}>
              <span className="material-symbols-outlined text-xs">add</span>
              <span>Add</span>
            </button>
          </div>

          <div className="zones-card-list">
            {zones.length === 0 ? (
              <div className="empty-zones-card">
                <span className="material-symbols-outlined empty-icon">crop_free</span>
                <h4>No Virtual Zones Configured</h4>
                <p>Define restricted polygons or buffer zones on camera {selectedCameraId || 'sensor'} to begin automated boundary tripwire alerts.</p>
                <button className="btn-primary btn-small" onClick={openEditor} style={{ marginTop: '12px' }}>
                  <span className="material-symbols-outlined text-xs">polyline</span>
                  <span>Draw First Polygon</span>
                </button>
              </div>
            ) : (
              zones.map((zone) => {
                const isRestricted = zone.zone_type === 'restricted';

                return (
                  <div key={zone.zone_id} className={`zone-tactical-card ${isRestricted ? 'zone-card-restricted' : 'zone-card-buffer'}`}>
                    <div className="zone-card-header">
                      <div>
                        <h4 className="zone-card-name">{zone.name}</h4>
                        <span className="zone-card-id">ID: {zone.zone_id}</span>
                      </div>
                      <span className={`status-pill ${isRestricted ? 'status-ERROR' : 'status-ONLINE'}`}>
                        {zone.zone_type ? zone.zone_type.toUpperCase() : 'ARMED'}
                      </span>
                    </div>

                    <div className="zone-card-body">
                      <div className="zone-meta-row">
                        <span className="zone-meta-label">TARGETS:</span>
                        <div className="zone-tags-wrap">
                          {zone.target_categories?.map((cat, i) => (
                            <span key={i} className="badge-class">{cat}</span>
                          ))}
                        </div>
                      </div>
                      <div className="zone-meta-row">
                        <span className="zone-meta-label">VERTICES ({zone.coordinates?.length || 0}):</span>
                        <div className="coords-box">
                          {zone.coordinates?.map((pt, i) => (
                            <span key={i} className="coord-chip">V{i + 1}: [{Math.round(pt.x)}, {Math.round(pt.y)}]</span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="zone-card-actions">
                      <span className="zone-armed-status">
                        <span className="zone-status-dot" />
                        Armed &amp; Monitoring
                      </span>
                      <button className="btn-small btn-danger" onClick={() => handleDeleteZone(zone.zone_id)} title="Delete Virtual Zone">
                        <span className="material-symbols-outlined text-xs">delete</span>
                        <span>Delete</span>
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
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
    </div>
  );
}
