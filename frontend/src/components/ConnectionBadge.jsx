import React from 'react';

export function ConnectionBadge({ status }) {
  const isConnected = status === 'CONNECTED';
  const isConnecting = status === 'CONNECTING';

  const dotClass = isConnected ? 'dot-connected' : isConnecting ? 'dot-connecting' : 'dot-disconnected';
  const badgeClass = isConnected ? 'badge-connected' : isConnecting ? 'badge-connecting' : 'badge-disconnected';

  return (
    <div className={`ws-badge ${badgeClass}`} title={`WebSocket: ${status}`}>
      <span className={`ws-dot ${dotClass}`} />
      <span>{status}</span>
    </div>
  );
}
