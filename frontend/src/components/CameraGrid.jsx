import React from 'react';
import { CameraTile } from './CameraTile';

export function CameraGrid({ cameras, healthMap, onStart, onStop, onExpand }) {
  if (!cameras || cameras.length === 0) {
    return (
      <div className="empty-grid">
        <div className="empty-grid-card">
          <span className="material-symbols-outlined empty-icon">videocam_off</span>
          <h3>No Surveillance Feeds Configured</h3>
          <p>Register an RTSP, USB Webcam, or Video stream in the Cameras console to initiate real-time boundary surveillance.</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`camera-grid ${cameras.length === 1 ? 'camera-grid-single' : cameras.length === 2 ? 'camera-grid-dual' : ''}`}>
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
