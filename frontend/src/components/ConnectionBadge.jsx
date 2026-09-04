import React from 'react';

export function ConnectionBadge({ status }) {
  const isConnected = status === 'CONNECTED';
  const isConnecting = status === 'CONNECTING';

  const dotClass = isConnected ? 'dot-connected' : isConnecting ? 'dot-connecting' : 'dot-disconnected';
  const badgeClass = isConnected ? 'badge-connected' : isConnecting ? 'badge-connecting' : 'badge-disconnected';

  const label = status ? status.charAt(0).toUpperCase() + status.slice(1).toLowerCase() : '';

  return (
    <div className={`ws-badge ${badgeClass}`} title={`Telemetry WebSocket: ${status}`}>
      <span className={`ws-dot ${dotClass}`} />
      <span>Telemetry: {label}</span>
    </div>
  );
}
