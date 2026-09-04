# VICENTRA / IBVAP — Project Context

## Project Purpose

IBVAP (Intelligent Border Video Analytics Platform), currently developed in the VICENTRA repository, is a software-defined AI video analytics platform built on top of ordinary IP CCTV infrastructure.

The system is intended to transform conventional CCTV streams into an intelligent surveillance network capable of detecting, tracking, and analysing objects and events without requiring dedicated smart cameras.

The long-term system capabilities include:

- Person detection and tracking
- Vehicle detection and classification
- Face detection and recognition
- Automatic Number Plate Recognition (ANPR)
- Virtual-fence intrusion detection
- Suspicious-activity and night-movement detection
- Real-time alerts and event logging
- Command dashboard with live feeds and incident history

The preferred deployment model is edge-first: video is processed locally where possible, while metadata and events can be transmitted to a central command system.

---

# Core Architecture

The intended high-level pipeline is:

```text
IP CCTV / RTSP / Video Source
        ↓
Video Ingestion & Stream Manager
        ↓
AI Inference Engine
        ↓
Tracking & Analytics
        ↓
Event & Alert Engine
        ↓
Database / Notifications / Command Dashboard
```

Each phase should integrate with the output of the previous phase rather than duplicating its responsibilities.

---

# Phase 1 — Video Ingestion

Phase 1 provides the AI-ready video ingestion foundation.

The pipeline is:

```text
Camera / RTSP / Video Source
        ↓
StreamWorker
        ↓
FrameSampler
        ↓
FrameBuffer
        ↓
FrameProvider
```

Key responsibilities include:

- Connecting to cameras and video sources
- Reading frames using OpenCV
- Handling reconnection with backoff
- Sampling frames to a suitable processing rate
- Maintaining bounded, thread-safe frame buffers
- Providing downstream consumers with access to frames

`FrameProvider` is the public integration boundary for downstream processing.

Downstream modules should consume frames through the public `FrameProvider` interface rather than directly accessing internal capture workers or buffers.

Phase 1 must not be unnecessarily redesigned or replaced by later phases.

---

# Phase 2 — AI Inference

Phase 2 consumes frames produced by Phase 1 and performs object detection.

The intended integration pipeline is:

```text
FrameProvider
        ↓
Background Inference Loop
        ↓
Object Detector / YOLO
        ↓
Detection Parser
        ↓
Standardized Detection Results
        ↓
Bounded Result Store
        ↓
API / Annotated Frames
```

Phase 2 is responsible for:

- Person detection
- Vehicle detection and original vehicle classification
- Confidence scores
- Bounding boxes
- Camera and frame metadata preservation
- Annotated frame generation without replacing original frames
- Per-camera recent detection storage
- Multi-camera-capable architecture
- Inference metrics and performance monitoring
- CUDA-first device selection with CPU fallback
- Robust error handling and logging

Detection results should preserve metadata such as:

```text
camera_id
timestamp
frame_id
class_id
class_name
category
confidence
bounding_box
relevant frame metadata
```

Raw image data should not be included in detection JSON.

---

# Phase 3 — Object Tracking

Phase 3 builds upon Phase 2 by associating bounding boxes across consecutive frames and assigning persistent tracking identities to objects. 

The integration pipeline is:

```text
Standardized Detection Results (ResultStore)
        ↓
Background Tracking Loop
        ↓
Object Tracker (Centroid matching)
        ↓
TrackedObject States
        ↓
TrackedStore (Bounded)
        ↓
API / Future Event Engine
```

Phase 3 introduces the following core rules:
- Tracking should not run inside the Video Ingestion loops or the Inference loops to avoid blocking them. Instead, it polls the Phase 2 `ResultStore`.
- Tracks are camera-isolated. Cross-camera tracking is not currently supported.
- `TrackedStore` is the public boundary for fetching the latest tracked objects.

---

# Phase 4 — Virtual Fences, Zones & Intrusion Detection

Phase 4 builds upon Phase 3 by evaluating tracked object positions against camera-specific Virtual Zones (polygons) and emitting state-transition security events.

The integration pipeline is:

```text
TrackedObject States (TrackedStore)
        ↓
Background Zone Evaluation Loop (Ray-Casting Algorithm)
        ↓
State Transition Logic (Outside ↔ Inside)
        ↓
Event Generator (ENTER / EXIT / INTRUSION)
        ↓
EventStore (Bounded) & DB Persistence (Zones)
        ↓
API / Zone & Event Overlays on Annotated Frames
```

Phase 4 introduces the following core rules:
- Ray-casting polygon intersection algorithm tests object ground position (bottom-center of bounding box) against zones belonging strictly to that camera.
- State transitions (`Outside → Inside` => `ENTER` / `INTRUSION`, `Inside → Outside` => `EXIT`) are strictly deduplicated so continuous presence generates no duplicate events.
- Expired track states are automatically purged from evaluation loops to prevent memory leaks.
- `EventStore` is the public boundary for fetching recent security intrusion events.

---

# Phase 5 — Real-Time Alerts & Event Engine

Phase 5 delivers security events created by Phase 4 to connected dashboard clients in real time via WebSocket broadcast, eliminating the need for frontend polling.

The integration pipeline is:

```text
Security Event Created (ZoneEvaluationLoop)
        ↓
EventStore.add_event() [on_event callback hook]
        ↓
EventDispatcher (In-process thread-safe dispatcher)
        ↓
WebSocket ConnectionManager (Broadcasts to active clients)
        ↓
Connected Dashboard Clients (/api/events/ws)
        ↓
🚨 Real-Time Security Alert UI
```

Phase 5 introduces the following core rules:
- Event creation remains strictly owned by Phase 4; Phase 5 handles only delivery.
- EventStore hooks into the EventDispatcher via a lightweight non-blocking callback hook (`on_event`).
- Dispatching from background daemon threads to async WebSockets is bridged safely using `asyncio.run_coroutine_threadsafe`.
- Connection failure or slow send on one client is isolated and will not block surveillance pipeline processing or other clients.
- Broken connections are automatically pruned to prevent memory leaks.
- Client reconnection uses exponential backoff to handle server restarts smoothly without polling loops.

---

# Phase 6 — Windows EXE Packaging & Deployment

Phase 6 packages the complete Phase 1–5 pipeline into a distributable Windows application using PyInstaller's one-directory distribution mode.

The packaging architecture is:

```text
Developer runs build script (scripts/build_windows.ps1)
        ↓
PyInstaller compiles (vicentra.spec)
        ↓
dist/VICENTRA/ one-directory distribution
        ↓
Operator double-clicks VICENTRA.exe
        ↓
Bootstrap (app/bootstrap.py)
  → Single-instance lock check
  → Port availability check
  → Uvicorn server launch (background thread)
  → Health-check readiness polling (/api/health)
  → Automatic browser launch
        ↓
Dashboard available at http://localhost:8000/
```

Phase 6 introduces the following core rules:
- Read-only application resources (static assets, model weights) are resolved via `get_resource_path()` which uses `sys._MEIPASS` in packaged mode.
- Writable user data (SQLite database, logs, runtime locks) is stored in `%LOCALAPPDATA%/VICENTRA/` via `get_data_dir()`.
- Single-instance enforcement prevents duplicate launches via PID-based file locks.
- The web dashboard remains the user interface; no native desktop GUI is created.
- One-directory distribution avoids the 30s+ unpacking penalty of one-file mode for large PyTorch/OpenCV binaries.

---

# Architecture Rules

The following rules apply to all future phases:

1. Do not create duplicate RTSP or video ingestion pipelines.
2. Do not bypass the public integration interfaces of completed phases.
3. Do not block video capture with AI inference, tracking, analytics, or HTTP requests.
4. Long-running processing should run in background workers or managed loops.
5. Support multiple cameras architecturally, even if the initial demo uses one camera.
6. Preserve important metadata as data moves between phases.
7. Use bounded and thread-safe in-memory storage where recent results are maintained.
8. Avoid unnecessary redesign of completed phases.
9. Use configuration or environment variables for configurable behavior rather than hardcoding values.
10. Implement robust logging and error handling so failures do not crash the entire application.
11. Add tests for new functionality and avoid breaking existing tests.
12. Make focused, reviewable changes rather than rewriting large parts of the repository.

---

# Development Workflow

Before implementing a new phase or major feature:

```text
Inspect existing code
        ↓
Identify integration boundaries
        ↓
Create concise implementation plan
        ↓
Review / approve plan
        ↓
Implement focused changes
        ↓
Run tests
        ↓
Review changes
        ↓
Commit and push
```

Agents and developers should inspect the actual repository before assuming class names, folder structures, APIs, or lifecycle behavior.

Repository documentation provides architectural context, but the existing source code remains the source of truth for implementation details.

---

# Current Product Direction

The preferred MVP is a complete end-to-end surveillance story rather than many incomplete features:

```text
CCTV
        ↓
Person / Vehicle Detection
        ↓
Object Tracking
        ↓
Virtual Fence
        ↓
Intrusion Event
        ↓
Alert
        ↓
Command Dashboard
```

Future phases should prioritize integration with this end-to-end story.

---

# Documentation Usage

Coding agents working on the repository should:

1. Read this `PROJECT_CONTEXT.md`.
2. Read `docs/PROJECT_STATUS.md`.
3. Read relevant architecture documentation.
4. Inspect the existing source code.
5. Identify actual integration points before modifying code.

This context defines project direction and architectural constraints. The repository implementation defines the current concrete interfaces and behavior.
