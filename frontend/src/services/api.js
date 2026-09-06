/**
 * Centralized REST API client for VICENTRA / IBVAP
 * Handles dev proxy or direct origin requests without trailing slashes.
 */

const BASE_URL = import.meta.env.VITE_API_BASE || '';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);

  if (response.status === 204) {
    return null;
  }

  if (!response.ok) {
    let errorDetail = `Request failed: ${response.status} ${response.statusText}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // Ignore JSON parse error on non-json response
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // --- System Health ---
  getHealth: () => request('/api/health'),

  // --- Cameras ---
  getCameras: () => request('/api/cameras'),
  getCamera: (id) => request(`/api/cameras/${encodeURIComponent(id)}`),
  createCamera: (data) => request('/api/cameras', { method: 'POST', body: JSON.stringify(data) }),
  updateCamera: (id, data) => request(`/api/cameras/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCamera: (id) => request(`/api/cameras/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  startCamera: (id) => request(`/api/cameras/${encodeURIComponent(id)}/start`, { method: 'POST' }),
  stopCamera: (id) => request(`/api/cameras/${encodeURIComponent(id)}/stop`, { method: 'POST' }),
  getCameraHealth: (id) => request(`/api/cameras/${encodeURIComponent(id)}/health`),

  // --- Video Frames ---
  getFrameUrl: (id, annotated = true) => {
    return `${BASE_URL}/api/cameras/${id}/frame${annotated ? '/annotated' : ''}?t=${Date.now()}`;
  },

  // --- AI Detections & Metrics ---
  getDetections: (id, limit = 50) => request(`/api/cameras/${id}/detections?limit=${limit}`),
  getAiStatus: () => request('/api/ai/status'),

  // --- Tracking ---
  getTracking: (id) => request(`/api/tracking/${id}`),
  getTrackingStatus: () => request('/api/tracking/status/all'),

  // --- Zones ---
  getZones: (cameraId) => request(`/api/cameras/${cameraId}/zones`),
  createZone: (cameraId, data) => request(`/api/cameras/${cameraId}/zones`, { method: 'POST', body: JSON.stringify(data) }),
  updateZone: (zoneId, data) => request(`/api/zones/${zoneId}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteZone: (zoneId) => request(`/api/zones/${zoneId}`, { method: 'DELETE' }),

  // --- Events ---
  getEvents: (params = {}) => {
    const query = new URLSearchParams();
    if (params.cameraId) query.append('camera_id', params.cameraId);
    if (params.zoneId) query.append('zone_id', params.zoneId);
    if (params.eventType) query.append('event_type', params.eventType);
    if (params.limit) query.append('limit', params.limit);
    const qs = query.toString();
    return request(`/api/events${qs ? `?${qs}` : ''}`);
  },
  clearEvents: (params = {}) => {
    const query = new URLSearchParams();
    if (params.cameraId) query.append('camera_id', params.cameraId);
    if (params.zoneId) query.append('zone_id', params.zoneId);
    const qs = query.toString();
    return request(`/api/events${qs ? `?${qs}` : ''}`, { method: 'DELETE' });
  },
};
