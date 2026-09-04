import React from 'react';
import { CameraTile } from './CameraTile';

export function CameraGrid({ cameras, healthMap, onStart, onStop, onExpand }) {
  if (!cameras || cameras.length === 0) {
    return (
      <div className="empty-grid">
        <div className="empty-grid-card">
          <span className="empty-icon">📹</span>
          <h3>No Cameras Registered</h3>
          <p>Add an RTSP, Webcam, or Video stream in the Cameras section to begin monitoring.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="camera-grid">
      {cameras.map((camera) => (
        <CameraTile
          key={camera.camera_id}
          camera={camera}
          health={healthMap[camera.camera_id]}
          onStart={onStart}
          onStop={onStop}
          onExpand={onExpand}
        />
      ))}
    </div>
  );
}
