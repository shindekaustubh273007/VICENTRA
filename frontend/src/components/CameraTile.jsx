import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';

export function CameraTile({ camera, health, onStart, onStop, onExpand }) {
  const [frameUrl, setFrameUrl] = useState('');
  const [hasFrameError, setHasFrameError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const intervalRef = useRef(null);

  const isOnline = health?.status === 'ONLINE';

  useEffect(() => {
    if (!isOnline) {
      setFrameUrl('');
      setHasFrameError(false);
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

  return (
    <div
      className={`camera-tile ${isOnline ? 'tile-online' : 'tile-offline'}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="tile-header">
        <div className="tile-title-group">
          <span className="camera-id">{camera.camera_id}</span>
          <span className="camera-name">{camera.name}</span>
        </div>
        <span className={`status-pill status-${status}`}>{status}</span>
      </div>

      <div className="tile-viewport" onClick={() => isOnline && onExpand?.(camera, frameUrl)}>
        {isOnline && !hasFrameError ? (
          <img
            src={frameUrl}
            alt={`${camera.name} live feed`}
            className="feed-image"
            onError={() => setHasFrameError(true)}
          />
        ) : (
          <div className="viewport-placeholder">
            <span className="placeholder-icon">{status === 'ERROR' ? '⚠️' : '📷'}</span>
            <span className="placeholder-text">
              {isOnline && hasFrameError
                ? 'Frame unavailable'
                : status === 'STOPPED'
                ? 'Stream Stopped'
                : status === 'DISABLED'
                ? 'Camera Disabled'
                : 'Connecting to Video Feed...'}
            </span>
          </div>
        )}

        {/* Overlaid metadata bar */}
        <div className="tile-meta-overlay">
          <span>{fps} / {targetFps} FPS</span>
          <span>{resolution}</span>
        </div>
      </div>

      <div className="tile-actions">
        {isOnline ? (
          <button className="btn-tile btn-danger" onClick={() => onStop?.(camera.camera_id)}>
            Stop
          </button>
        ) : (
          <button className="btn-tile btn-success" onClick={() => onStart?.(camera.camera_id)}>
            Start
          </button>
        )}
        <button
          className="btn-tile btn-secondary"
          onClick={() => onExpand?.(camera, frameUrl)}
          disabled={!isOnline}
        >
          Expand
        </button>
      </div>
    </div>
  );
}
