import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

export function CameraTile({ camera, health, onStart, onStop, onExpand }) {
  const [frameUrl, setFrameUrl] = useState('');
  const [hasFrameError, setHasFrameError] = useState(false);
  const intervalRef = useRef(null);

  const isOnline = health?.status === 'ONLINE';

  useEffect(() => {
    if (!isOnline) {
      return;
    }

    const refreshFrame = () => {
      setFrameUrl(api.getFrameUrl(camera.camera_id, true));
      setHasFrameError(false);
    };

    refreshFrame();
    // Refresh frame every 1s for smooth preview without overloading backend
    intervalRef.current = setInterval(refreshFrame, 1000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [camera.camera_id, isOnline]);

  const status = health?.status || (camera.enabled ? 'CONNECTING' : 'STOPPED');
  const fps = health?.current_fps ?? 0;
  const targetFps = camera.target_fps || 5;
  const resolution = health?.resolution || '--';
  const formattedStatus = status ? status.charAt(0).toUpperCase() + status.slice(1).toLowerCase() : '';
  const sourceType = camera.source_type ? camera.source_type.charAt(0).toUpperCase() + camera.source_type.slice(1).toLowerCase() : '';

  return (
    <div className={`camera-tile ${isOnline ? 'tile-online' : 'tile-offline'}`}>
      {/* Tactical 4-Corner Targeting Reticles [ + ] */}
      <span className="tile-corner-tr" />
      <span className="tile-corner-bl" />

      <div className="tile-header">
        <div className="tile-title-group">
          <span className="camera-id">{camera.camera_id}</span>
          <span className="camera-name">{camera.name}</span>
        </div>
        <span className={`status-pill status-${status}`}>{formattedStatus}</span>
      </div>

      <div
        className="tile-viewport"
        onClick={() => isOnline && onExpand?.(camera, frameUrl)}
        title={isOnline ? 'Click to inspect / enlarge feed' : undefined}
      >
        {isOnline && !hasFrameError ? (
          <img
            src={frameUrl}
            alt={`${camera.name} live feed`}
            className="feed-image"
            onError={() => setHasFrameError(true)}
          />
        ) : (
          <div className="viewport-placeholder">
            <span className="material-symbols-outlined placeholder-icon">
              {status === 'ERROR' ? 'warning' : 'videocam_off'}
            </span>
            <span className="placeholder-text">
              {isOnline && hasFrameError
                ? 'Signal Dropped'
                : status === 'STOPPED'
                ? 'Stream Standby'
                : status === 'DISABLED'
                ? 'Sensor Disabled'
                : 'Acquiring Video Link...'}
            </span>
          </div>
        )}

        {/* Overlaid tactical metadata bar */}
        <div className="tile-meta-overlay">
          <span>{fps.toFixed ? fps.toFixed(1) : fps} / {targetFps} fps</span>
          <span>{resolution !== '--' ? `${resolution} • ` : ''}{sourceType}</span>
        </div>
      </div>

      <div className="tile-actions">
        {isOnline ? (
          <button className="btn-tile btn-danger" onClick={() => onStop?.(camera.camera_id)}>
            Stop Feed
          </button>
        ) : (
          <button className="btn-tile btn-success" onClick={() => onStart?.(camera.camera_id)}>
            Start Feed
          </button>
        )}
        <button
          className="btn-tile btn-secondary"
          onClick={() => onExpand?.(camera, frameUrl)}
          disabled={!isOnline}
        >
          Inspect
        </button>
      </div>
    </div>
  );
}
