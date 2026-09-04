import React, { useState, useEffect, useRef } from 'react';

// Synthesize a tactical radar alert tone using the Web Audio API without needing external mp3 assets
function playAlertChime() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.25);
    gain.gain.setValueAtTime(0.15, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.25);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.25);
  } catch {
    // AudioContext blocked or not supported
  }
}

export function EventFeed({ events, onClear }) {
  const [soundEnabled, setSoundEnabled] = useState(false);
  const prevEventCountRef = useRef(events.length);

  useEffect(() => {
    if (soundEnabled && events.length > prevEventCountRef.current) {
      const newest = events[0];
      if (newest?.event_type === 'INTRUSION') {
        playAlertChime();
      }
    }
    prevEventCountRef.current = events.length;
  }, [events, soundEnabled]);

  const formatTime = (ts) => {
    if (!ts) return '--:--:--';
    const date = new Date(ts);
    return date.toLocaleTimeString();
  };

  return (
    <aside className="event-feed-panel">
      <div className="event-feed-header">
        <div>
          <div className="feed-title-row">
            <span className="material-symbols-outlined text-sm" style={{ color: events.some(e => e.event_type === 'INTRUSION') ? 'var(--neon-crimson)' : 'var(--status-emerald)' }}>
              {events.some(e => e.event_type === 'INTRUSION') ? 'priority_high' : 'radar'}
            </span>
            <span className="feed-title">Tactical Alert Stream</span>
            <span className="feed-badge">{events.length}</span>
          </div>
          <div className="feed-subtitle">Live Intrusion &amp; Boundary Telemetry</div>
        </div>

        <div className="feed-controls">
          <button
            className={`btn-icon ${soundEnabled ? 'active' : ''}`}
            onClick={() => setSoundEnabled(!soundEnabled)}
            title={soundEnabled ? 'Mute Alert Tone' : 'Arm Audio Siren'}
          >
            <span className="material-symbols-outlined text-base">
              {soundEnabled ? 'volume_up' : 'volume_off'}
            </span>
          </button>
          <button className="btn-small btn-secondary" onClick={onClear} title="Acknowledge & clear queue">
            Ack All
          </button>
        </div>
      </div>

      <div className="event-list">
        {events.length === 0 ? (
          <div className="empty-events">
            <span className="material-symbols-outlined empty-icon" style={{ color: 'var(--status-emerald)' }}>
              security
            </span>
            <p>Perimeter Secure</p>
            <small>Active radar mesh listening for boundary intrusions...</small>
          </div>
        ) : (
          events.map((evt) => {
            const isIntrusion = evt.event_type === 'INTRUSION';
            const isEnter = evt.event_type === 'ENTER';

            const typeClass = isIntrusion
              ? 'alert-intrusion'
              : isEnter
              ? 'alert-enter'
              : 'alert-exit';

            return (
              <div key={evt.event_id || `${evt.camera_id}_${evt.timestamp}`} className={`alert-card ${typeClass}`}>
                <div className="alert-card-top">
                  <span className={`alert-tag tag-${evt.event_type}`}>
                    {isIntrusion ? 'Critical intrusion' : isEnter ? 'Zone entry' : 'Zone exit'}
                  </span>
                  <span className="alert-time">{formatTime(evt.timestamp)}</span>
                </div>

                <div className="alert-card-body">
                  <div className="alert-primary">
                    <strong className="alert-object">{evt.object_class || 'Entity'}</strong>
                    <span className="alert-track-id">#{evt.track_id}</span>
                  </div>
                  <div className="alert-secondary">
                    <span>Camera: <strong>{evt.camera_id}</strong></span>
                    <span>Zone: <strong>{evt.zone_name || evt.zone_id}</strong></span>
                  </div>
                </div>

                {evt.position && (
                  <div className="alert-pos">
                    Grid: [{Math.round(evt.position.x)}, {Math.round(evt.position.y)}]
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </aside>
  );
}
