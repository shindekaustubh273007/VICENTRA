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
| Phase 3 | Tracking & Analytics                | Next / In Planning                           |
| Phase 4 | ANPR / Face / Specialized Detection | Not Started                                  |
| Phase 5 | Event & Alert Engine                | Not Started                                  |
| Phase 6 | Command Dashboard                   | Not Started                                  |
| Phase 7 | Integration, Testing & Final Demo   | Not Started                                  |
| Phase 8 | Windows Packaging & Deployment      | Not Started                                  |

> Important: Before marking Phase 2 as fully complete, verify its actual implementation and test status in the repository. Documentation must match the source code.

---

# Completed Phase 1 — Video Ingestion

Phase 1 provides the foundation for all downstream processing.

## Data Flow

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

## Confirmed Responsibilities

Phase 1 provides:

- Video source connection.
- Frame capture.
- Reconnection and failure recovery.
- Frame sampling.
- Bounded frame buffering.
- Thread-safe frame access.
- Public frame access for downstream consumers.
- Camera/frame metadata.

## Integration Rule

Downstream phases should use the existing public `FrameProvider` interface to consume frames.

Do not create:

- A second RTSP connection for AI.
- A separate camera capture pipeline.
- Direct dependencies on internal worker buffers unless explicitly exposed by the repository.

---

# Phase 2 — AI Inference

## Intended Data Flow

```text
FrameProvider
        ↓
InferenceLoop
        ↓
Object Detector
        ↓
Detection Parser
        ↓
Standardized Detection Results
        ↓
ResultStore
        ↓
API / Annotated Frames
```

## Intended Responsibilities

Phase 2 is responsible for:

- Person detection.
- Vehicle detection.
- Original model vehicle class preservation where available.
- Higher-level categories.
- Confidence scores.
- Bounding boxes.
- Camera ID preservation.
- Timestamp preservation.
- Frame ID preservation.
- Relevant frame metadata preservation.
- Annotated frames.
- Recent detection result storage.
- Multi-camera-capable design.
- Inference metrics.
- CUDA-first processing where available.
- CPU fallback.
- Configuration through environment variables.
- Logging and error handling.
- API integration.
- Tests and documentation.

## Explicitly Outside Phase 2

The following belong to later phases:

- Persistent object tracking.
- Virtual fence logic.
- Intrusion detection.
- ANPR.
- Face recognition.
- Suspicious behavior detection.
- Alert generation.
- Permanent event storage.
- Major command dashboard development.

---

# Immediate Next Phase — Phase 3

## Phase Name

**Tracking & Analytics**

## Primary Objective

Extend the existing detection pipeline by associating object detections across frames and maintaining persistent object identities.

The basic flow should become:

```text
Camera
  ↓
Phase 1 — Frame Ingestion
  ↓
Phase 2 — Object Detection
  ↓
Standardized Detections
  ↓
Phase 3 — Object Tracking
  ↓
Persistent Track IDs
  ↓
Tracking Analytics
```

## Phase 3 Core Goals

Phase 3 should investigate and implement, based on the actual repository architecture:

- Persistent tracking IDs.
- Detection association across frames.
- Per-camera tracker state.
- Track creation and lifecycle management.
- Track updates.
- Handling temporary missed detections.
- Track expiration.
- Object position history.
- Movement information where useful.
- Tracked-object result storage.
- API integration.
- Track visualization or annotated frames where useful.
- Tests.

## Architectural Constraints

Phase 3 must:

1. Consume the output of completed phases rather than duplicate them.
2. Preserve camera separation.
3. Avoid blocking video capture.
4. Avoid redesigning Phase 1 unnecessarily.
5. Avoid replacing the Phase 2 detection system.
6. Use the actual repository interfaces.
7. Keep recent state bounded.
8. Support multiple cameras architecturally.
9. Keep tracking independent from HTTP request execution.
10. Add focused tests for the new functionality.

---

# Phase 3 Discovery Checklist

Before implementation, inspect the repository and determine:

```text
[ ] Exact FrameProvider interface
[ ] Exact detection result schema
[ ] Exact inference result storage interface
[ ] Camera lifecycle and startup hooks
[ ] Background worker architecture
[ ] Current FastAPI application structure
[ ] Existing configuration system
[ ] Existing logging conventions
[ ] Existing test structure
[ ] Current Phase 2 completion status
```

Do not implement Phase 3 based only on assumptions from documentation.

---

# Recommended Next Action

The next coding-agent or developer task should be repository discovery only.

Recommended workflow:

```text
1. Read PROJECT_CONTEXT.md
        ↓
2. Read docs/ARCHITECTURE.md
        ↓
3. Read this PROJECT_STATUS.md
        ↓
4. Inspect Phase 1 and Phase 2 source code
        ↓
5. Identify exact integration points
        ↓
6. Return concise Phase 3 implementation plan
        ↓
7. Review and approve the plan
        ↓
8. Implement in small, testable increments
```

The first implementation should be a small vertical slice rather than the entire Phase 3 system at once.

A recommended first milestone is:

```text
Existing Detection Results
        ↓
Single-Camera Tracker
        ↓
Persistent Track IDs
        ↓
Tracked Result Store
        ↓
One API Endpoint
        ↓
Tests
```

After that works correctly, expand toward:

```text
Multi-camera management
        ↓
Track history
        ↓
Movement analytics
        ↓
Virtual fence integration
```

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
