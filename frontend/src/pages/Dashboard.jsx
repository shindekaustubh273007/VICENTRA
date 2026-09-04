import React, { useState } from 'react';
import { CameraGrid } from '../components/CameraGrid';
import { EventFeed } from '../components/EventFeed';
import { MetricCard } from '../components/MetricCard';

export function Dashboard({ cameras, healthMap, globalHealth, events, onStart, onStop, onClearEvents }) {
  const [activeModal, setActiveModal] = useState(null);

  const activeStreamsCount = globalHealth?.active_streams ?? 0;
  const totalStreamsCount = globalHealth?.total_managed ?? cameras.length;
  const intrusionCount = events.filter((e) => e.event_type === 'INTRUSION').length;

  return (
    <div className="dashboard-container">
      {/* Top Telemetry Metric Bar */}
      <section className="metrics-row">
        <MetricCard
          title="Active Streams"
          value={`${activeStreamsCount} / ${totalStreamsCount}`}
          subtitle="Online CCTV feeds"
          icon="📹"
          variant="primary"
        />
        <MetricCard
          title="Intrusion Alerts"
          value={intrusionCount}
          subtitle="Restricted zone triggers"
          icon="🚨"
          variant={intrusionCount > 0 ? 'danger' : 'success'}
        />
        <MetricCard
          title="Recent Events"
          value={events.length}
          subtitle="Live session total"
          icon="⚡"
        />
        <MetricCard
          title="System Engine"
          value={globalHealth?.status || 'OFFLINE'}
          subtitle="Inference & Analytics"
          icon="⚙️"
          variant={globalHealth?.status === 'UP' ? 'success' : 'danger'}
        />
      </section>

      {/* Main Content Area: Feeds + Alert Feed */}
      <div className="dashboard-main">
        <section className="feeds-section">
          <div className="section-header">
            <h2>Live Surveillance Feeds</h2>
            <span className="live-indicator">● LIVE ANNOTATED</span>
          </div>

          <CameraGrid
            cameras={cameras}
            healthMap={healthMap}
            onStart={onStart}
            onStop={onStop}
            onExpand={(cam, url) => setActiveModal({ cam, url })}
          />
        </section>

        <EventFeed events={events} onClear={onClearEvents} />
      </div>

      {/* Fullscreen Video Modal */}
      {activeModal && (
        <div className="modal-backdrop" onClick={() => setActiveModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>{activeModal.cam.name}</h3>
                <span className="modal-sub">ID: {activeModal.cam.camera_id} — {activeModal.cam.location}</span>
              </div>
              <button className="btn-close" onClick={() => setActiveModal(null)}>✕</button>
            </div>
            <div className="modal-body">
              <img
                src={activeModal.url}
                alt={activeModal.cam.name}
                className="modal-image"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
