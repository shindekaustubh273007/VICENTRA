"""
Phase 5 — WebSocket Endpoint for Real-Time Security Events.

Route: /api/events/ws
Connects dashboard clients and streams live ZoneEvents as they occur.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import ws_manager
from app.core.logging import logger

router = APIRouter()


@router.websocket("/ws")
@router.websocket("/ws/")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time security events.
    Clients connect to receive live ENTER, EXIT, and INTRUSION events as they occur.
    """
    connected = await ws_manager.connect(websocket)
    if not connected:
        return

    try:
        while True:
            # Keepalive / receive messages (e.g. client heartbeats/pings)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await ws_manager.disconnect(websocket)
