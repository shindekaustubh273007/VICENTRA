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
          title="Surveillance Feeds"
          value={`${activeStreamsCount} / ${totalStreamsCount}`}
          subtitle="Synchronized live video mesh"
          icon="videocam"
          variant="primary"
        />
        <MetricCard
          title="Perimeter Threat Status"
          value={intrusionCount > 0 ? `${intrusionCount} breach detected` : 'Perimeter secure'}
          subtitle={intrusionCount > 0 ? 'Restricted zone intrusion' : 'Boundary perimeter intact'}
          icon="warning"
          variant={intrusionCount > 0 ? 'danger' : 'success'}
        />
        <MetricCard
          title="Tracked Target Events"
          value={events.length}
          subtitle="Real-time telemetry queue"
          icon="radar"
        />
        <MetricCard
          title="Edge Neural Pipeline"
          value={globalHealth?.status === 'UP' ? 'Online' : 'Offline'}
          subtitle="Inference &amp; Object Tracker"
          icon="memory"
          variant={globalHealth?.status === 'UP' ? 'success' : 'danger'}
        />
      </section>

      {/* Main Content Area: Hero Feeds + Live Alert Triage */}
      <div className="dashboard-main">
        <section className="feeds-section">
          <div className="section-header">
            <h2>
              <span className="material-symbols-outlined text-sm">grid_view</span>
              Surveillance Grid Matrix
            </h2>
            <span className="live-indicator">● Live annotated</span>
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
                <span className="modal-sub">ID: {activeModal.cam.camera_id} • Location: {activeModal.cam.location}</span>
              </div>
              <button className="btn-close" onClick={() => setActiveModal(null)} title="Close Viewport">✕</button>
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
