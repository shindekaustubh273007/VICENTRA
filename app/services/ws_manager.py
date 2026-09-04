"""
Phase 5 — WebSocket Connection Manager.

Manages the lifecycle of active WebSocket clients. Handles registration,
clean disconnection, error isolation, and broadcasting of ZoneEvents to all
active clients.
"""

import asyncio
from typing import Set
from fastapi import WebSocket
from app.core.logging import logger
from app.core.config import settings
from app.services.event_store import ZoneEvent


class ConnectionManager:
    """
    Manages active WebSocket client connections and broadcasts real-time security events.
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> bool:
        """
        Accept and register a new WebSocket connection if within client limits.
        """
        if len(self.active_connections) >= settings.WS_MAX_CLIENTS:
            logger.warning(
                f"WebSocket connection rejected: max client limit ({settings.WS_MAX_CLIENTS}) reached."
            )
            await websocket.close(code=1008, reason="Max client limit reached")
            return False

        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)

        try:
            from app.services.event_dispatcher import event_dispatcher
            event_dispatcher.set_loop(asyncio.get_running_loop())
        except Exception:
            pass

        logger.info(f"WebSocket client connected. Total active: {len(self.active_connections)}")
        return True

    async def disconnect(self, websocket: WebSocket):
        """
        Unregister a WebSocket connection.
        """
        async with self._lock:
            self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total active: {len(self.active_connections)}")

    async def broadcast(self, event: ZoneEvent):
        """
        Broadcast a security event to all connected clients.
        Each client send is isolated: failure on one client will not block others.
        """
        message = {
            "type": "security_event",
            "event": event.to_dict(),
        }

        async with self._lock:
            connections = list(self.active_connections)

        if not connections:
            return

        broken_connections = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send event to WebSocket client: {e}")
                broken_connections.append(connection)

        if broken_connections:
            async with self._lock:
                for broken in broken_connections:
                    self.active_connections.discard(broken)
            logger.info(
                f"Cleaned up {len(broken_connections)} broken connection(s). Total active: {len(self.active_connections)}"
            )

    async def disconnect_all(self):
        """
        Close all active connections during server shutdown.
        """
        async with self._lock:
            connections = list(self.active_connections)
            self.active_connections.clear()

        for connection in connections:
            try:
                await connection.close(code=1001, reason="Server shutting down")
            except Exception:
                pass
        logger.info("All WebSocket connections closed.")


# Module-level singleton
ws_manager = ConnectionManager()
