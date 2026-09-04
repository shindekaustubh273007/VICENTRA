# VICENTRA / IBVAP — Architecture

## 1. System Overview

VICENTRA / IBVAP is designed as a modular AI video analytics platform built on top of existing IP CCTV infrastructure.

The architecture follows a sequential processing pipeline in which each phase has a clear responsibility and exposes an integration boundary for the next phase.

```text
IP CCTV / RTSP / Video Source
        │
        ▼
┌──────────────────────────────┐
│ Phase 1                      │
│ Video Ingestion              │
└──────────────────────────────┘
        │
        ▼
      FrameProvider
        │
        ▼
┌──────────────────────────────┐
│ Phase 2                      │
│ AI Inference                 │
└──────────────────────────────┘
        │
        ▼
 Standardized Detection Results
        │
        ▼
┌──────────────────────────────┐
│ Phase 3                      │
│ Tracking & Analytics         │
└──────────────────────────────┘
        │
        ▼
 Analytics / Tracking Events
        │
        ▼
┌──────────────────────────────┐
│ Phase 4+                     │
│ Specialized Detection        │
│ Event & Alert Processing     │
└──────────────────────────────┘
        │
        ▼
┌──────────────────────────────┐
│ Command Dashboard            │
└──────────────────────────────┘
```

---

# 2. Phase 1 — Video Ingestion Architecture

Phase 1 is responsible only for acquiring and preparing video frames for downstream consumers.

The data flow is:

```text
Camera / RTSP / Local Video / Webcam
        │
        ▼
StreamWorker
        │
        ▼
FrameSampler
        │
        ▼
FrameBuffer
        │
        ▼
FrameProvider
```

## Component Responsibilities

### StreamWorker

Responsible for:

- Connecting to the configured video source.
- Reading frames using the existing video capture mechanism.
- Handling temporary connection failures.
- Reconnecting using backoff logic.
- Running independently from downstream AI processing.

A slow inference or tracking process must not block the video capture loop.

---

### FrameSampler

Responsible for:

- Reducing the native camera frame rate to a suitable processing rate.
- Preventing unnecessary downstream processing.
- Allowing the system to operate efficiently on available hardware.

---

### FrameBuffer

Responsible for:

- Holding a bounded number of recent frames.
- Providing thread-safe access.
- Automatically discarding old frames when the buffer reaches capacity.

The system should not allow unbounded frame accumulation.

---

### FrameProvider

`FrameProvider` is the primary integration boundary between Phase 1 and downstream modules.

Downstream consumers should obtain frames through the existing public interface, conceptually:

```text
FrameProvider.get_latest_frame(camera_id)
```

Future phases must not directly depend on internal stream worker buffers unless the repository explicitly exposes such behavior as part of a public interface.

---

# 3. Phase 2 — AI Inference Architecture

Phase 2 consumes frames provided by Phase 1 and converts them into standardized object detections.

The intended data flow is:

```text
FrameProvider
        │
        ▼
Inference Manager
        │
        ├──────────── Camera A ────────────┐
        │                                  ▼
        ├──────────── Camera B ───────► InferenceLoop
        │                                  │
        │                                  ▼
        │                            Model / Detector
        │                                  │
        │                                  ▼
        │                            Detection Parser
        │                                  │
        └──────────────────────────────────┘
                                           │
                                           ▼
                              Standardized Detections
                                           │
                                           ▼
                                      ResultStore
                                           │
                              ┌────────────┴────────────┐
                              ▼                         ▼
                         API Results             Annotated Frames
```

## Component Responsibilities

### Inference Manager

Responsible for:

- Managing inference workers or loops.
- Supporting multiple cameras architecturally.
- Starting and stopping inference processing cleanly.
- Coordinating inference lifecycle with the application.

---

### InferenceLoop

Responsible for:

- Continuously retrieving the latest available frame.
- Avoiding unnecessary processing of stale frames.
- Passing frames to the detector.
- Running independently from HTTP request handling.
- Recording inference metrics.

Inference should not be performed directly inside API request handlers.

---

### Model Manager / Detector

Responsible for:

- Loading the object detection model.
- Selecting the available processing device.
- Preferring CUDA when available.
- Falling back safely to CPU.
- Executing model inference.

---

### Detection Parser

Responsible for converting model-specific output into a stable project-level detection structure.

Downstream phases should depend on the standardized detection representation rather than directly depending on YOLO-specific result objects.

---

### ResultStore

Responsible for:

- Maintaining recent inference results.
- Supporting retrieval by camera.
- Using bounded storage.
- Providing thread-safe access where required.

Phase 2 results are intended to be consumed by APIs and future analytics modules.

---

# 4. Standard Detection Data Boundary

The detection result is the primary integration boundary between Phase 2 and Phase 3.

Conceptually, each detection contains:

```text
camera_id
timestamp
frame_id

class_id
class_name
category

confidence

bounding_box
    x1
    y1
    x2
    y2

relevant frame metadata
```

Example:

```json
{
  "camera_id": "BOP-01",
  "timestamp": "2026-09-02T10:30:21.234Z",
  "frame_id": "BOP-01_00001234",
  "class_id": 0,
  "class_name": "person",
  "category": "person",
  "confidence": 0.94,
  "bounding_box": {
    "x1": 420,
    "y1": 180,
    "x2": 570,
    "y2": 720
  }
}
```

Raw image data should not be embedded inside detection JSON.

If Phase 3 requires access to image frames for a tracking algorithm, it should use an existing public frame interface rather than adding a duplicate video ingestion system.

---

# 5. Phase 3 — Tracking & Analytics Integration Boundary

Phase 3 builds on top of Phase 2.

The implemented architecture is:

```text
Phase 1
FrameProvider
        │
        ▼
Phase 2
Object Detection
        │
        ▼
Standardized Detection Results (ResultStore)
        │
        ▼
Phase 3
Tracking Manager (Manages per-camera TrackingLoops)
        │
        ▼
TrackingLoop (polls ResultStore)
        │
        ▼
Object Tracker (Centroid/IOU Association)
        │
        ├── Persistent Track ID
        ├── Object State
        ├── Position History
        ├── Track Lifecycle
        │
        ▼
TrackedStore (Bounded per-camera storage)
        │
        ▼
FastAPI Tracking Endpoints (/api/v1/tracking)
```

The exact implementation uses `TrackingLoop` to poll the `ResultStore` for new frame timestamps, ensuring that tracking does not block the upstream inference or video ingestion threads.

Before implementing Phase 3, inspect:

1. The actual Phase 1 `FrameProvider` interface.
2. The actual Phase 2 detection schema.
3. How camera IDs, timestamps, and frame IDs are generated.
4. Existing worker and lifecycle management.
5. Existing result storage patterns.
6. Existing FastAPI application structure.

Do not assume class or method names from this document are exact implementation contracts.

---

# 6. Phase 3 Architectural Responsibilities

Phase 3 should focus on:

```text
Detection
    │
    ▼
Association Across Frames
    │
    ▼
Persistent Object Identity
    │
    ▼
Track State and History
    │
    ▼
Analytics
```

Potential tracked object data:

```text
track_id
camera_id
class_name
category

current_bounding_box
current_position

first_seen
last_seen

position_history
track_age
```

A tracking identity should generally remain associated with the same object across consecutive detections while the tracker considers the association valid.

The implementation should define appropriate track lifecycle behavior, including:

- Track creation.
- Detection-to-track association.
- Track update.
- Temporary missed detections.
- Track expiration or removal.

---

# 7. Phase 4 — Virtual Fences, Zones & Intrusion Detection Architecture

Phase 4 introduces virtual zones and security intrusion event detection on top of Phase 3 tracked objects.

The data flow is:

```text
Phase 3 TrackedStore
        │
        ▼
ZoneManager (Orchestrates per-camera ZoneEvaluationLoops)
        │
        ▼
ZoneEvaluationLoop (Polls TrackedStore)
        │
        ▼
Zone Geometry (Ray-Casting Algorithm for Point-in-Polygon)
        │
        ▼
State Transition Logic (Outside ↔ Inside)
        │
        ├── State Change: False → True  => Emit ENTER (and INTRUSION if restricted)
        └── State Change: True → False  => Emit EXIT
        │
        ▼
EventStore (Bounded per-camera storage) & DB (SQLite persistence for zones)
        │
        ▼
FastAPI Endpoints (/api/v1/zones, /api/v1/events) & Zone Overlays on Annotated Frames
```

### Component Responsibilities

#### ZoneStore (`app/services/zone_store.py`)
- Maintains thread-safe in-memory cache of configured zones per camera.
- Loaded from SQLite database on startup via `ZoneManager.load_zones_from_db()`.

#### ZoneGeometry (`app/services/zone_geometry.py`)
- Implements Ray-Casting algorithm (`point_in_polygon`) for point-in-polygon checks.
- Computes bottom-center `((x1 + x2) / 2.0, y2)` evaluation point from object bounding box.

#### ZoneEvaluationLoop (`app/services/zone_evaluation_loop.py`)
- Polling daemon thread per camera running at `ZONE_EVALUATION_FPS`.
- Evaluates object ground positions against camera-specific zones.
- Maintains `zone_states` map `(zone_id, track_id) -> is_inside`.
- Evaluates state transitions to deduplicate events: continuous presence inside a zone generates zero duplicate events.
- Automatically cleans up state for expired tracks.

#### EventStore (`app/services/event_store.py`)
- Thread-safe bounded deque per camera (`ZONE_MAX_EVENTS_PER_CAMERA`) and globally.
- Stores `ZoneEvent` objects (`event_id`, `event_type`, `camera_id`, `zone_id`, `zone_name`, `track_id`, `object_class`, `category`, `timestamp`, `position`).
- Exposes `on_event` callback hook for dispatching newly added events to downstream subscribers.

---

# 8. Phase 5 — Real-Time Alerts & Event Engine Architecture

Phase 5 introduces real-time event dispatching and WebSocket streaming to command dashboard clients.

The data flow is:

```text
Phase 4 Security Event Created
        │
        ▼
EventStore.add_event(event)
        │
        ├── In-Memory Storage (Bounded Deques)
        │
        ▼
on_event Callback Hook
        │
        ▼
EventDispatcher (`app/services/event_dispatcher.py`)
        │ (asyncio.run_coroutine_threadsafe)
        ▼
WebSocket ConnectionManager (`app/services/ws_manager.py`)
        │
        ├── Client Broadcast Loop (Isolated send per client)
        │
        ▼
Active WebSocket Clients (`/api/events/ws`)
        │
        ▼
Command Dashboard UI (`static/index.html`)
        │
        ▼
🚨 Live Alert Feed & Visual Notifications
```

### Component Responsibilities

#### EventDispatcher (`app/services/event_dispatcher.py`)
- In-process, thread-safe publish-subscribe engine.
- Bridges synchronous daemon worker threads (`ZoneEvaluationLoop`) to async event subscribers.
- Safely schedules coroutines on the running asyncio event loop via `asyncio.run_coroutine_threadsafe`.
- Maintains thread-safe subscriber registry with exception isolation.

#### WebSocket ConnectionManager (`app/services/ws_manager.py`)
- Manages active client `WebSocket` connections (`set`).
- Enforces maximum concurrent client limits (`WS_MAX_CLIENTS`).
- Broadcasts standardized JSON security messages:
  ```json
  {
    "type": "security_event",
    "event": {
      "event_id": "...",
      "event_type": "INTRUSION",
      "camera_id": "...",
      "zone_id": "...",
      "zone_name": "...",
      "track_id": "...",
      "object_class": "person",
      "category": "person",
      "timestamp": "...",
      "position": {"x": 100.0, "y": 200.0}
    }
  }
  ```
- Error isolation: if a client connection fails or drops, it is pruned without blocking other clients or the surveillance pipeline.
- Gracefully disconnects all clients on server shutdown (`disconnect_all`).

#### WebSocket Endpoint (`app/api/ws.py`)
- Route: `/api/events/ws` (and `/api/events/ws/`).
- Accepts connections, registers with `ConnectionManager`, and listens for keepalives/pings.
- Unregisters cleanly on disconnect or socket drop.

#### Dashboard Client Integration (`static/index.html`)
- Live Security Alerts panel with real-time connection status pill (`CONNECTED`, `CONNECTING`, `DISCONNECTED`).
- Real-time DOM rendering of `INTRUSION` (red), `ENTER` (amber), and `EXIT` (gray) alerts.
- Bounded DOM list (`MAX_DASHBOARD_ALERTS = 50`) prevents browser memory bloat.
- Automatic reconnection with exponential backoff (1s → 2s → 4s → max 30s) handles backend restarts automatically.

---

# 9. Phase 6 — Windows EXE Packaging & Deployment Architecture

Phase 6 packages the complete application into a distributable Windows executable using PyInstaller's one-directory mode.

The packaging and runtime data flow is:

```text
Build Time:
  vicentra.spec (PyInstaller config)
         │
         ▼
  scripts/build_windows.ps1
         │
         ▼
  dist/VICENTRA/
         ├── VICENTRA.exe
         └── _internal/
              ├── static/          (bundled dashboard assets)
              ├── yolov8n.pt       (bundled YOLO model)
              └── (Python runtime, DLLs, packages)

Runtime:
  VICENTRA.exe
         │
         ▼
  launcher.py → app.bootstrap.main()
         │
         ├── SingleInstanceLock (%LOCALAPPDATA%/VICENTRA/runtime/vicentra.lock)
         │
         ├── Port Check → find_available_port()
         │
         ├── Uvicorn Server (background thread)
         │         │
         │         ▼
         │    app.main:app (FastAPI)
         │
         ├── Health Polling → wait_for_server_ready(/api/health)
         │
         └── Browser Launch → webbrowser.open()
```

### Component Responsibilities

#### Centralized Paths (`app/core/paths.py`)
- `get_base_dir()`: Returns `sys._MEIPASS` in frozen mode, repo root in development.
- `get_resource_path(relative)`: Resolves read-only bundled resources (static assets, models).
- `get_data_dir()`: Returns `%LOCALAPPDATA%/VICENTRA` for writable data (SQLite, logs, locks).
- `get_database_url()`: SQLite URL pointing to writable data directory.
- `get_model_path(name)`: Multi-strategy model resolution (direct → bundled → user models → fallback).

#### Application Bootstrap (`app/bootstrap.py`)
- Single-instance enforcement via PID-based file locks.
- Port availability check with automatic fallback to next available port.
- Programmatic Uvicorn server launch in a daemon thread.
- HTTP health-check polling before browser launch.
- Graceful shutdown on SIGINT/SIGTERM/Ctrl+C with lock cleanup.

#### Build Tooling
- `vicentra.spec`: PyInstaller configuration bundling `static/`, `yolov8n.pt`, and all hidden imports.
- `scripts/build_windows.ps1`: Automated build script with environment check, clean, build, and verification.
- `launcher.py`: Minimal PyInstaller entry point delegating to `app.bootstrap.main()`.

---

# 10. Multi-Camera Principle

The architecture should support multiple cameras.

Tracking state must not accidentally mix detections from different cameras.

Conceptually:

```text
Camera A
    │
    ├── Detection Results
    │         │
    │         ▼
    │    Tracker A
    │
Camera B
    │
    ├── Detection Results
    │         │
    │         ▼
    │    Tracker B
```

A `track_id` should therefore be managed with clear camera context unless future cross-camera tracking is explicitly implemented.

Phase 3 should not claim to provide cross-camera identity tracking unless that functionality is intentionally designed and implemented.

---

# 11. Concurrency Principles

The pipeline contains multiple processing stages.

```text
Video Capture
      │
      ▼
Frame Sampling
      │
      ▼
AI Inference
      │
      ▼
Tracking
      │
      ▼
Analytics
```

Each stage should avoid unnecessarily blocking earlier stages.

Important rules:

- Video capture must not wait for tracking.
- Tracking should not block HTTP requests.
- Long-running processing should operate through background workers, loops, queues, or equivalent architecture consistent with the existing repository.
- Shared state must be handled safely.
- Recent result stores must remain bounded.

The exact concurrency model should integrate with the existing implementation rather than introducing an unrelated architecture.

---

# 12. API and Visualization Boundaries

The backend may expose tracked objects and analytics through API endpoints.

Conceptual flow:

```text
Tracking / Analytics Result
        │
        ▼
Result Store
        │
        ▼
FastAPI Endpoint
        │
        ▼
Dashboard / Demo Client
```

Future visualization may include:

```text
Original Frame
        +
Detection Bounding Box
        +
Track ID
        +
Object Label
        +
Analytics / Zone Overlay
```

Visualization must operate on copies or derived frames where appropriate and should not overwrite the original frame used by the pipeline.

---

# 13. Phase Boundaries

The architecture separates responsibilities by phase.

```text
Phase 1
Video acquisition

Phase 2
Object detection

Phase 3
Object tracking and analytics

Phase 4
Virtual fences, zones & intrusion detection

Phase 5
Real-time alerts & event engine

Phase 6
Windows EXE packaging & deployment
```

A future phase should consume outputs from previous phases rather than reimplementing them.

---

# 14. Core Architectural Rules

All future development should follow these principles:

1. Preserve completed phase behavior unless a deliberate integration change is required.
2. Do not duplicate RTSP or camera ingestion.
3. Use public integration boundaries.
4. Keep long-running processing outside HTTP request handlers.
5. Maintain camera identity throughout the pipeline.
6. Preserve timestamps and frame identity where available.
7. Keep in-memory stores bounded.
8. Support multiple cameras architecturally.
9. Avoid coupling downstream modules directly to model-specific data structures.
10. Keep responsibilities separated by phase.
11. Prefer focused extensions over large rewrites.
12. Inspect the repository before making assumptions about implementation details.

---

# Source of Truth

This document describes the intended architecture and integration boundaries.

The actual repository source code is the source of truth for:

- Current class names.
- File and folder structure.
- Existing interfaces.
- Lifecycle behavior.
- API routes.
- Data schemas.

Any implementation must inspect the current code before modifying or extending the system.
