import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function useTracking(cameraId, pollIntervalMs = 2000) {
  const [tracks, setTracks] = useState([]);
  const [detections, setDetections] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchTracking = useCallback(async () => {
    if (!cameraId) {
      setTracks([]);
      setDetections([]);
      return;
    }

    try {
      const [trackRes, detectRes] = await Promise.all([
        api.getTracking(cameraId).catch(() => ({ tracks: [] })),
        api.getDetections(cameraId, 20).catch(() => ({ detections: [] })),
      ]);

      setTracks(trackRes.tracks || []);
      setDetections(detectRes.detections || []);
    } catch {
      // Stream or camera might be inactive
    } finally {
      setLoading(false);
    }
  }, [cameraId]);

  useEffect(() => {
    setLoading(true);
    fetchTracking();

    if (pollIntervalMs > 0 && cameraId) {
      const timer = setInterval(fetchTracking, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [fetchTracking, pollIntervalMs, cameraId]);

  return { tracks, detections, loading, refresh: fetchTracking };
}
