"""
Unit and Integration tests for Phase 5 Real-Time Alerts & Event Engine.

Tests EventDispatcher, WebSocket ConnectionManager, /api/events/ws endpoint,
error isolation, multiple client broadcasts, and lifecycle management.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.services.event_store import ZoneEvent, EventStore, event_store
from app.services.event_dispatcher import EventDispatcher, event_dispatcher
from app.services.ws_manager import ConnectionManager, ws_manager


def _create_sample_event(
    event_id: str = "evt-001",
    event_type: str = "INTRUSION",
    camera_id: str = "CAM-WS-01",
) -> ZoneEvent:
    return ZoneEvent(
        event_id=event_id,
        event_type=event_type,
        camera_id=camera_id,
        zone_id="ZONE-FENCE",
        zone_name="Perimeter Fence",
        track_id="T-99",
        object_class="person",
        category="person",
        timestamp=datetime(2026, 9, 3, 14, 30, 0),
        position=(150.0, 200.0),
    )


# ── 1. EventDispatcher Unit Tests ──────────────────────────────────────

def test_event_dispatcher_sync_callback():
    """Verify sync subscribers receive published events."""
    dispatcher = EventDispatcher()
    received = []

    def on_event(evt: ZoneEvent):
        received.append(evt)

    dispatcher.subscribe(on_event)
    sample_evt = _create_sample_event()
    dispatcher.publish(sample_evt)

    assert len(received) == 1
    assert received[0].event_id == "evt-001"
    assert received[0].event_type == "INTRUSION"

    # Unsubscribe test
    dispatcher.unsubscribe(on_event)
    dispatcher.publish(sample_evt)
    assert len(received) == 1  # No duplicate or new delivery


def test_event_dispatcher_error_isolation():
    """Failing subscriber does not prevent other subscribers from receiving event."""
    dispatcher = EventDispatcher()
    received = []

    def bad_callback(evt: ZoneEvent):
        raise RuntimeError("Subscriber crashed!")

    def good_callback(evt: ZoneEvent):
        received.append(evt)

    dispatcher.subscribe(bad_callback)
    dispatcher.subscribe(good_callback)

    sample_evt = _create_sample_event()
    dispatcher.publish(sample_evt)

    assert len(received) == 1
    assert received[0].event_id == "evt-001"


# ── 2. Event Schema Validation ─────────────────────────────────────────

def test_zone_event_schema_to_dict():
    """Verify ZoneEvent dictionary serialization format."""
    evt = _create_sample_event()
    data = evt.to_dict()

    assert data["event_id"] == "evt-001"
    assert data["event_type"] == "INTRUSION"
    assert data["camera_id"] == "CAM-WS-01"
    assert data["zone_id"] == "ZONE-FENCE"
    assert data["zone_name"] == "Perimeter Fence"
    assert data["track_id"] == "T-99"
    assert data["object_class"] == "person"
    assert data["category"] == "person"
    assert data["timestamp"] == "2026-09-03T14:30:00"
    assert data["position"] == {"x": 150.0, "y": 200.0}


# ── 3. ConnectionManager Unit Tests ───────────────────────────────────

@pytest.mark.anyio
async def test_connection_manager_broadcast_and_isolation():
    """Verify broadcast delivers to all clients and discards broken clients."""
    manager = ConnectionManager()

    good_client = AsyncMock()
    broken_client = AsyncMock()
    broken_client.send_json.side_effect = RuntimeError("Broken pipe")

    # Connect clients
    await manager.connect(good_client)
    await manager.connect(broken_client)
    assert len(manager.active_connections) == 2

    # Broadcast event
    evt = _create_sample_event()
    await manager.broadcast(evt)

    # Verify good client received message
    good_client.send_json.assert_called_once()
    sent_msg = good_client.send_json.call_args[0][0]
    assert sent_msg["type"] == "security_event"
    assert sent_msg["event"]["event_id"] == "evt-001"

    # Verify broken client was removed
    assert broken_client not in manager.active_connections
    assert good_client in manager.active_connections
    assert len(manager.active_connections) == 1

    # Cleanup
    await manager.disconnect_all()
    assert len(manager.active_connections) == 0


@pytest.mark.anyio
async def test_connection_manager_max_client_limit():
    """Verify client limit is enforced."""
    manager = ConnectionManager()
    from app.core.config import settings
    orig_limit = settings.WS_MAX_CLIENTS
    try:
        settings.WS_MAX_CLIENTS = 1
        c1 = AsyncMock()
        c2 = AsyncMock()

        assert await manager.connect(c1) is True
        assert await manager.connect(c2) is False
        c2.close.assert_called_once()
    finally:
        settings.WS_MAX_CLIENTS = orig_limit
        await manager.disconnect_all()


# ── 4. EventStore on_event Callback Integration ────────────────────────

def test_event_store_on_event_callback():
    """Verify event_store.add_event triggers on_event hook without duplicates."""
    store = EventStore(max_per_camera=10)
    dispatched = []

    store.on_event = lambda evt: dispatched.append(evt)

    evt = _create_sample_event()
    store.add_event(evt)

    assert len(dispatched) == 1
    assert dispatched[0].event_id == "evt-001"
    assert len(store.get_events()) == 1


# ── 5. WebSocket Integration Tests with FastAPI TestClient ─────────────

def test_websocket_endpoint_connect_and_receive():
    """Verify client connects to /api/events/ws and receives live event broadcast."""
    event_dispatcher.subscribe(ws_manager.broadcast)
    client = TestClient(app)

    with client.websocket_connect("/api/events/ws") as websocket:
        # Publish an event through singleton dispatcher
        sample_evt = _create_sample_event(event_id="ws-test-1", event_type="INTRUSION")
        event_dispatcher.publish(sample_evt)

        # Receive JSON message over WebSocket
        data = websocket.receive_json()
        assert data["type"] == "security_event"
        assert data["event"]["event_id"] == "ws-test-1"
        assert data["event"]["event_type"] == "INTRUSION"
        assert data["event"]["camera_id"] == "CAM-WS-01"


@pytest.mark.anyio
async def test_multiple_clients_receive_broadcast():
    """Verify multiple connected clients both receive the broadcast."""
    manager = ConnectionManager()
    client1 = AsyncMock()
    client2 = AsyncMock()

    await manager.connect(client1)
    await manager.connect(client2)
    assert len(manager.active_connections) == 2

    sample_evt = _create_sample_event(event_id="multi-1", event_type="ENTER")
    await manager.broadcast(sample_evt)

    client1.send_json.assert_called_once()
    client2.send_json.assert_called_once()

    msg1 = client1.send_json.call_args[0][0]
    msg2 = client2.send_json.call_args[0][0]

    assert msg1["event"]["event_id"] == "multi-1"
    assert msg2["event"]["event_id"] == "multi-1"
    assert msg1["event"]["event_type"] == "ENTER"
    assert msg2["event"]["event_type"] == "ENTER"

    await manager.disconnect_all()
    assert len(manager.active_connections) == 0


def test_websocket_endpoint_sequential_clients():
    """Verify endpoint handles consecutive client connections and deliveries cleanly."""
    event_dispatcher.subscribe(ws_manager.broadcast)
    client = TestClient(app)

    # Client A connects, receives event, disconnects
    with client.websocket_connect("/api/events/ws") as ws_a:
        evt_a = _create_sample_event(event_id="ws-seq-a", event_type="ENTER")
        event_dispatcher.publish(evt_a)
        data_a = ws_a.receive_json()
        assert data_a["event"]["event_id"] == "ws-seq-a"

    # Client B connects, receives next event, disconnects
    with client.websocket_connect("/api/events/ws") as ws_b:
        evt_b = _create_sample_event(event_id="ws-seq-b", event_type="INTRUSION")
        event_dispatcher.publish(evt_b)
        data_b = ws_b.receive_json()
        assert data_b["event"]["event_id"] == "ws-seq-b"


def test_rest_events_endpoint_still_works():
    """Verify existing REST endpoint /api/events continues to function normally."""
    client = TestClient(app)

    # Add an event through event_store
    evt = _create_sample_event(event_id="rest-test-1", event_type="INTRUSION", camera_id="REST-CAM")
    event_store.add_event(evt)

    response = client.get("/api/events?camera_id=REST-CAM")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    events = [e for e in data["events"] if e["event_id"] == "rest-test-1"]
    assert len(events) == 1
    assert events[0]["event_type"] == "INTRUSION"

    # Cleanup
    event_store.clear("REST-CAM")


def test_end_to_end_phase4_event_creation_to_websocket():
    """
    Integration test:
    Phase 4 Zone Event Created -> event_store.add_event() -> EventDispatcher -> WebSocket Client.
    """
    event_dispatcher.subscribe(ws_manager.broadcast)
    event_store.on_event = event_dispatcher.publish
    client = TestClient(app)

    with client.websocket_connect("/api/events/ws") as websocket:
        # Simulate Phase 4 ZoneEvaluationLoop emitting an INTRUSION event
        intrusion_evt = _create_sample_event(
            event_id="e2e-intrusion-99",
            event_type="INTRUSION",
            camera_id="E2E-CAM",
        )
        event_store.add_event(intrusion_evt)

        # Receive real-time push over WebSocket
        msg = websocket.receive_json()
        assert msg["type"] == "security_event"
        assert msg["event"]["event_id"] == "e2e-intrusion-99"
        assert msg["event"]["event_type"] == "INTRUSION"
        assert msg["event"]["camera_id"] == "E2E-CAM"

        # Also verify event is stored in EventStore for historical queries
        stored = event_store.get_events(camera_id="E2E-CAM")
        assert len(stored) >= 1
        assert stored[-1].event_id == "e2e-intrusion-99"

    event_store.clear("E2E-CAM")
