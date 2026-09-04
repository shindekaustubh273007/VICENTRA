# VICENTRA / IBVAP — Project Status

> This document records the current implementation state of the project.
>
> Update this file when a phase is completed, when a major architectural decision changes, or when a significant known issue is discovered.
>
> `PROJECT_CONTEXT.md` contains stable project context. This file contains the changing project state.

---

# Current Status

**Project:** VICENTRA / IBVAP — Intelligent Border Video Analytics Platform

**Current Development Stage:** Phase 6 — Windows EXE Packaging & Deployment (Complete)

**Overall Goal:** Build an AI-powered video analytics layer on top of ordinary IP CCTV infrastructure.

**Current MVP Direction:**

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
Real-Time Alert
  ↓
Command Dashboard
  ↓
Windows EXE Distribution
```

The priority is to build one convincing end-to-end surveillance workflow rather than implementing every planned feature independently.

---

# Phase Status

| Phase   | Name                                | Status    |
| ------- | ----------------------------------- | --------- |
| Phase 1 | Video Ingestion & Stream Manager    | Completed |
| Phase 2 | AI Inference Engine                 | Completed |
| Phase 3 | Tracking & Analytics                | Completed |
| Phase 4 | Virtual Fences, Zones & Intrusion   | Completed |
| Phase 5 | Real-Time Alerts & Event Engine     | Completed |
| Phase 6 | Windows EXE Packaging & Deployment  | Completed |

---

# Completed Phase 6 — Windows EXE Packaging & Deployment

Phase 6 packages the complete Phase 1–5 pipeline into a distributable Windows application that an operator can launch by double-clicking `VICENTRA.exe`.

## Implemented Responsibilities

- **Centralized Path Resolution (`app/core/paths.py`)**: Separates read-only bundled resources (`sys._MEIPASS` / `get_resource_path()`) from writable runtime data (`%LOCALAPPDATA%/VICENTRA` / `get_data_dir()`). Provides `get_database_url()` and `get_model_path()` for consistent resolution in both development and packaged environments.
- **Application Bootstrap (`app/bootstrap.py`)**: Manages the complete launch lifecycle — single-instance enforcement via PID-based file locks, port availability check with fallback, programmatic Uvicorn server launch in a background thread, HTTP health-check readiness polling, automatic default browser launch, and graceful shutdown on SIGINT/SIGTERM.
- **PyInstaller Entry Point (`launcher.py`)**: Minimal launcher script that delegates to `app.bootstrap.main()`.
- **PyInstaller Configuration (`vicentra.spec`)**: One-directory distribution bundling `static/` assets, `yolov8n.pt` model, Ultralytics package data, and all hidden imports for FastAPI/Uvicorn/PyTorch/OpenCV.
- **Build Automation (`scripts/build_windows.ps1`)**: Reproducible build script with environment check, clean, PyInstaller invocation, and distribution verification (executable + static assets + model in `_internal/`).
- **Updated Core Services**: `config.py`, `logging.py`, `main.py`, and `detector.py` all use centralized path resolution for seamless operation in packaged mode.
- **Automated Tests (`tests/test_packaging.py`)**: 7 tests covering resource path resolution (dev + frozen modes), data directory creation, database URL generation, model path resolution, single-instance lock, and port helpers.

## Distribution Layout

```text
dist/VICENTRA/
├── VICENTRA.exe           (Application executable)
└── _internal/
    ├── static/            (Dashboard HTML/CSS/JS)
    ├── yolov8n.pt         (YOLO model weights)
    └── (Python runtime, DLLs, packages)

%LOCALAPPDATA%/VICENTRA/   (Created at runtime)
├── data/ibvap.db          (SQLite database)
├── logs/                  (Application logs)
├── runtime/vicentra.lock  (Single-instance lock)
└── models/                (User-provided models)
```

---

# Completed Phase 5 — Real-Time Alerts & Event Engine

Phase 5 implements real-time security event delivery from Phase 4 to connected dashboard clients via WebSockets, eliminating polling.

## Implemented Responsibilities

- **`EventDispatcher` (`app/services/event_dispatcher.py`)**: Thread-safe in-process dispatcher bridging worker threads to async subscribers via `asyncio.run_coroutine_threadsafe`.
- **`ConnectionManager` (`app/services/ws_manager.py`)**: Manages active WebSocket connections with client limit enforcement (`WS_MAX_CLIENTS`), error isolation, and broadcast pruning.
- **WebSocket Endpoint (`app/api/ws.py`)**: Mounted at `/api/events/ws` for real-time push of security events.
- **`EventStore.on_event` Hook (`app/services/event_store.py`)**: Lightweight non-blocking callback hook bridging event creation in `add_event()` to the dispatcher.
- **Dashboard Live Alerts (`static/index.html`)**: Real-time alerts card with connection status badge (`CONNECTED`, `CONNECTING`, `DISCONNECTED`), visual styling for `INTRUSION`, `ENTER`, and `EXIT`, bounded DOM history (`50` items), and automatic reconnection with exponential backoff.
- **Automated Test Suite (`tests/test_websocket.py`)**: 10 unit and end-to-end integration tests covering dispatcher, schema, error isolation, single & multiple clients, client limits, and E2E event creation to WebSocket push.

---

# Known Architectural Decisions

The following decisions should be preserved unless the team explicitly revises them:

- Existing ordinary IP CCTV infrastructure is the video source.
- Processing is designed to be edge-first where practical.
- Phase 1 owns video ingestion.
- Downstream modules consume frames through the public integration boundary.
- AI inference should operate in background processing rather than inside HTTP requests.
- Tracking should consume standardized detection outputs rather than model-specific YOLO objects.
- Multi-camera support should be considered throughout the architecture.
- Recent in-memory data should be bounded.
- Raw image data should not be placed inside detection JSON.
- Configuration should avoid unnecessary hardcoded values.
- The preferred final demo is a complete detection → tracking → intrusion → alert → dashboard story.
- Read-only bundled resources are separated from writable runtime data via `app/core/paths.py`.
- Windows `.exe` packaging uses PyInstaller one-directory mode with `%LOCALAPPDATA%/VICENTRA` for writable data.

---

# Verification Before Starting Phase 3

Before Phase 3 implementation begins, confirm:

```text
[ ] Repository is up to date.
[ ] Correct branch is selected.
[ ] Phase 1 source is intact.
[ ] Phase 2 source exists and is committed.
[ ] Existing tests are identified.
[ ] Existing tests pass, or known failures are documented.
[ ] Current detection schema is confirmed from source code.
[ ] Current result retrieval mechanism is confirmed from source code.
```

---

# Phase 3 Completion Criteria

Phase 3 should not be marked complete until the implemented scope is defined and verified.

At minimum, the completed implementation should demonstrate:

```text
Detection across consecutive frames
        ↓
Same object receives a persistent tracking identity
        ↓
Track state updates correctly
        ↓
Multiple cameras remain isolated
        ↓
Missing detections are handled safely
        ↓
Expired tracks are removed
        ↓
Results can be retrieved through the existing application architecture
        ↓
Tests pass
```

Any additional analytics, such as virtual fences or movement rules, should be marked according to their actual implementation status rather than assumed complete.

---

# Update Procedure

At the end of every major phase:

1. Update the phase status table.
2. Move completed functionality into the appropriate completed-phase section.
3. Record actual integration interfaces.
4. Record any important architectural decisions.
5. Document known limitations or deferred features.
6. Define the next immediate phase.
7. Verify that the documentation matches the repository.
8. Commit documentation changes with the related implementation or as a separate documentation commit.

The repository source code remains the source of truth for exact implementation details.
