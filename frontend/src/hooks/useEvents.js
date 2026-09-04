import { useState, useEffect, useCallback } from 'react';
import { wsClient } from '../services/ws';
import { api } from '../services/api';

const MAX_EVENTS = 50;

export function useEvents(maxItems = MAX_EVENTS) {
  const [events, setEvents] = useState([]);
  const [wsStatus, setWsStatus] = useState('DISCONNECTED');
  const [loading, setLoading] = useState(true);

  // 1. Initial REST fetch for historical events
  useEffect(() => {
    let isMounted = true;
    api
      .getEvents({ limit: maxItems })
      .then((res) => {
        if (isMounted && res && res.events) {
          setEvents(res.events.slice(0, maxItems));
        }
      })
      .catch((err) => {
        console.warn('Could not fetch initial events:', err);
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [maxItems]);

  // 2. WebSocket live event subscription
  useEffect(() => {
    wsClient.connect();

    const unsubscribeStatus = wsClient.subscribeStatus((status) => {
      setWsStatus(status);
    });

    const unsubscribeEvents = wsClient.subscribe((newEvent) => {
      setEvents((prev) => {
        // Prevent exact duplicates if event_id already present
        if (prev.some((e) => e.event_id === newEvent.event_id)) {
          return prev;
        }
        const updated = [newEvent, ...prev];
        return updated.slice(0, maxItems);
      });
    });

    return () => {
      unsubscribeStatus();
      unsubscribeEvents();
    };
  }, [maxItems]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return {
    events,
    wsStatus,
    loading,
    clearEvents,
  };
}
