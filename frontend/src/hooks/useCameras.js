import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export function useCameras(pollIntervalMs = 3000) {
  const [cameras, setCameras] = useState([]);
  const [healthMap, setHealthMap] = useState({});
  const [globalHealth, setGlobalHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCameraData = useCallback(async () => {
    try {
      const [cams, healthRes] = await Promise.all([
        api.getCameras().catch(() => []),
        api.getHealth().catch(() => ({ status: 'DOWN', streams: [] })),
      ]);

      const map = {};
      if (healthRes && healthRes.streams) {
        healthRes.streams.forEach((h) => {
          map[h.camera_id] = h;
        });
      }

      setCameras(cams || []);
      setHealthMap(map);
      setGlobalHealth(healthRes);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to load cameras');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCameraData();
    if (pollIntervalMs > 0) {
      const timer = setInterval(fetchCameraData, pollIntervalMs);
      return () => clearInterval(timer);
    }
  }, [fetchCameraData, pollIntervalMs]);

  const startStream = async (id) => {
    await api.startCamera(id);
    await fetchCameraData();
  };

  const stopStream = async (id) => {
    await api.stopCamera(id);
    await fetchCameraData();
  };

  const deleteCamera = async (id) => {
    await api.deleteCamera(id);
    await fetchCameraData();
  };

  const createCamera = async (data) => {
    const res = await api.createCamera(data);
    await fetchCameraData();
    return res;
  };

  return {
    cameras,
    healthMap,
    globalHealth,
    loading,
    error,
    refresh: fetchCameraData,
    startStream,
    stopStream,
    deleteCamera,
    createCamera,
  };
}
