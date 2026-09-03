# VICENTRA / IBVAP — Project Status

> This document records the current implementation state of the project.
>
> Update this file when a phase is completed, when a major architectural decision changes, or when a significant known issue is discovered.
>
> `PROJECT_CONTEXT.md` contains stable project context. This file contains the changing project state.

---

# Current Status

**Project:** VICENTRA / IBVAP — Intelligent Border Video Analytics Platform

**Current Development Stage:** Phase 3 — Tracking & Analytics

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
Alert
  ↓
Command Dashboard
```

The priority is to build one convincing end-to-end surveillance workflow rather than implementing every planned feature independently.

---

# Phase Status

| Phase   | Name                                | Status                                       |
| ------- | ----------------------------------- | -------------------------------------------- |
| Phase 1 | Video Ingestion & Stream Manager    | Completed                                    |
| Phase 2 | AI Inference Engine                 | Completed / Repository Verification Required |
| Phase 3 | Tracking & Analytics                | Completed                                    |
| Phase 4 | ANPR / Face / Specialized Detection | Next / In Planning                           |

---

# Completed Phase 3 — Object Tracking

Phase 3 establishes the foundation for tracking objects over time by associating detections from Phase 2.

## Implemented Responsibilities

- **`TrackedObject`**: Schema representing objects over time, retaining history and assigning a `track_id`.
- **`ObjectTracker`**: A per-camera lightweight centroid-distance based association algorithm.
- **`TrackingLoop`**: A daemon thread that polls `ResultStore` to fetch the latest detections without blocking upstream layers.
- **`TrackedStore`**: A thread-safe bounded store for the latest tracked objects.
- **`TrackingManager`**: Orchestrates `TrackingLoop`s, tying their lifecycle to the FastAPI app.
- **API**: Exposed `GET /api/v1/tracking/{camera_id}` for clients.

## Explicitly Outside Phase 3

- **Virtual Fencing & Zone Intrusion**: Deferred to Phase 4/5 Event Engine.
- **Cross-Camera Tracking**: Deferred. Tracks are isolated per camera.

---

# Immediate Next Phase — Phase 4

## Phase Name

**Specialized Detection (ANPR / Face) & Event/Virtual Fence Engine**

## Primary Objective

Now that objects are tracked with persistence, the system should allow users to draw virtual zones (fences) and trigger events when tracked objects enter or cross them. Additionally, Phase 4 should explore extending detection models for License Plates (ANPR) or Faces where applicable.

## Recommended Next Action

The next step is to design the Event Engine that consumes `TrackedStore` or `TrackingLoop` outputs, checks for zone intersections using the position history, and emits `IntrusionEvent`s.

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
- Windows `.exe` packaging is a late-stage deployment concern after the system is integrated and working.

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
