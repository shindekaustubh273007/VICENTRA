# IBVAP - Video Ingestion & Stream Manager

This module is the foundation of the Intelligent Border Video Analytics Platform (IBVAP). It is responsible for reliable video stream ingestion, buffering, sampling, and providing frames to future AI modules.

## Architecture

```text
                ┌─────────────────┐
                │   IP CCTV #1    │
                └────────┬────────┘
                         │ RTSP
                ┌────────▼────────┐
                │                 │
                │ Stream Manager  │
                │                 │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │ Frame Buffer    │
                └────────┬────────┘
                         │
                ┌────────▼────────┐
                │ Frame Sampler   │
                └────────┬────────┘
                         │
                         ▼
                  FrameProvider
                         │
                         ▼
                 ┌───────────────┐
                 │ FUTURE AI     │
                 │ INFERENCE     │
                 └───────────────┘
```

The system manages independent `StreamWorker` threads for each camera. A `FrameBuffer` (thread-safe bounding queue) ensures low latency. The `FrameSampler` guarantees configurable target FPS. `FrameProvider` gives a clean abstraction for future downstream consumers.

## Installation

Create a virtual environment:

### Windows
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Running

Run the main application using:
```bash
python run.py
```

- **API Base URL**: `http://localhost:8000/api`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **Test Dashboard**: `http://localhost:8000/`

## Usage Examples

### Adding an RTSP camera
Use the dashboard or make a POST request to `/api/cameras`:
```json
{
    "camera_id": "BOP-01",
    "name": "Perimeter Cam",
    "location": "North",
    "source_type": "rtsp",
    "source_url": "rtsp://username:password@192.168.1.100:554/stream",
    "target_fps": 5,
    "buffer_size": 10
}
```

### Using a video file
```json
{
    "camera_id": "FILE-01",
    "name": "File Test",
    "location": "Local",
    "source_type": "file",
    "source_url": "./media/sample/test.mp4",
    "target_fps": 15
}
```
*(Note: Use `generate_video.py` to create a test mp4 file).*

### Using a webcam
```json
{
    "camera_id": "WEB-01",
    "name": "Laptop Cam",
    "location": "Desk",
    "source_type": "webcam",
    "source_url": "0",
    "target_fps": 5
}
```
