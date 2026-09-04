"""
Phase 5 — Event Dispatcher.

Thread-safe in-process event dispatching mechanism. Bridges thread-based
evaluations (ZoneEvaluationLoop) to async subscribers (WebSocket connections)
safely via asyncio.run_coroutine_threadsafe.
"""

import asyncio
import threading
from typing import Callable, List, Optional
from app.core.logging import logger
from app.services.event_store import ZoneEvent


class EventDispatcher:
    """
    In-process event dispatcher.
    Allows async or sync subscribers to register callbacks for security events.
    """

    def __init__(self):
        self._subscribers: List[Callable] = []
        self._lock = threading.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        """Set the active asyncio event loop for scheduling async deliveries."""
        self._loop = loop

    def subscribe(self, callback: Callable):
        """Register a callback (sync or async) for published events."""
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)
                logger.info(f"Subscribed {getattr(callback, '__name__', str(callback))} to EventDispatcher")

    def unsubscribe(self, callback: Callable):
        """Unregister a callback."""
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)
                logger.info(f"Unsubscribed {getattr(callback, '__name__', str(callback))} from EventDispatcher")

    def publish(self, event: ZoneEvent):
        """
        Publish an event to all subscribers.
        Thread-safe: can be safely invoked from daemon threads (e.g. ZoneEvaluationLoop).
        """
        with self._lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    if self._loop and self._loop.is_running():
                        asyncio.run_coroutine_threadsafe(callback(event), self._loop)
                    else:
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(callback(event))
                        except RuntimeError:
                            try:
                                asyncio.run(callback(event))
                            except Exception as loop_err:
                                logger.warning(f"Could not execute async subscriber: {loop_err}")
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in subscriber callback {callback}: {e}")

    def clear(self):
        """Clear all subscribers."""
        with self._lock:
            self._subscribers.clear()


# Module-level singleton
event_dispatcher = EventDispatcher()
