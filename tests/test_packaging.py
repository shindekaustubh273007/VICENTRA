"""
Unit and Integration tests for Phase 6 Windows Packaging & Deployment.

Tests resource path resolution, runtime writable data directories,
model path discovery, single-instance lock handling, and port checking.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.core.paths import (
    get_base_dir,
    get_resource_path,
    get_data_dir,
    get_database_url,
    get_model_path,
)
from app.bootstrap import SingleInstanceLock, is_port_in_use, find_available_port
from app.utils.video import parse_source


def test_resource_path_dev_mode():
    """Verify resource path resolves to repository root in development mode."""
    with patch.object(sys, "frozen", False, create=True):
        base_dir = get_base_dir()
        assert (base_dir / "app").is_dir()
        
        static_path = get_resource_path("static")
        assert static_path.is_dir()
        assert (static_path / "index.html").is_file()


def test_resource_path_frozen_mode():
    """Verify resource path resolves to sys._MEIPASS when packaged with PyInstaller."""
    fake_meipass = Path(tempfile.gettempdir()) / "fake_meipass_test"
    fake_meipass.mkdir(parents=True, exist_ok=True)

    try:
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "_MEIPASS", str(fake_meipass), create=True):
            resolved = get_resource_path("static")
            assert resolved == fake_meipass / "static"
    finally:
        if fake_meipass.exists():
            fake_meipass.rmdir()


def test_data_dir_resolution_and_creation():
    """Verify %LOCALAPPDATA%/VICENTRA directory resolution and subfolder creation."""
    data_dir = get_data_dir()
    assert data_dir.is_dir()
    assert (data_dir / "data").is_dir()
    assert (data_dir / "logs").is_dir()
    assert (data_dir / "runtime").is_dir()
    assert (data_dir / "models").is_dir()


def test_database_url_generation():
    """Verify database URL points to writable data directory."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("DATABASE_URL", None)
        db_url = get_database_url()
        assert db_url.startswith("sqlite:///")
        assert "ibvap.db" in db_url


def test_model_path_resolution():
    """Verify model path discovery resolves local yolov8n.pt."""
    model_path = get_model_path("yolov8n.pt")
    assert Path(model_path).is_file()
    assert model_path.endswith("yolov8n.pt")


def test_single_instance_lock():
    """Verify single instance lock prevents duplicate acquisition and cleans up on release."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / "test_vicentra.lock"
        lock1 = SingleInstanceLock(lock_file)
        lock2 = SingleInstanceLock(lock_file)

        # 1. First instance acquires
        assert lock1.acquire() is True
        assert lock_file.exists()

        # 2. Second instance fails to acquire while first is active
        assert lock2.acquire() is False

        # 3. First instance releases
        lock1.release()
        assert not lock_file.exists()

        # 4. Second instance can now acquire
        assert lock2.acquire() is True
        lock2.release()


def test_single_instance_lock_stale_pid():
    """Verify single instance lock detects dead/stale PID and re-acquires successfully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        lock_file = Path(tmpdir) / "test_vicentra_stale.lock"
        # Write a non-existent PID
        lock_file.write_text("999999", encoding="utf-8")

        lock = SingleInstanceLock(lock_file)
        # Should detect stale PID and acquire
        assert lock.acquire() is True
        assert lock_file.read_text(encoding="utf-8").strip() == str(os.getpid())
        lock.release()


def test_port_helpers():
    """Verify port detection and search helpers."""
    # Test checking a free port
    free_port = find_available_port("127.0.0.1", 59123)
    assert isinstance(free_port, int)
    assert 59123 <= free_port <= 59133


def test_spa_fallback_routes():
    """Verify that client-side SPA routes like /zones and /cameras return index.html on direct refresh."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    for route in ["/", "/zones", "/cameras", "/events"]:
        resp = client.get(route)
        assert resp.status_code == 200
        assert "root" in resp.text


def test_parse_source_relative_media_resolution():
    """Verify parse_source resolves relative ./media/sample paths to real absolute paths."""
    resolved = parse_source("./media/sample/test.mp4", "file")
    assert Path(resolved).is_file()
    assert resolved.endswith("test.mp4")

    # Webcam returns integer 0
    assert parse_source("0", "webcam") == 0

    # RTSP URLs remain unchanged
    rtsp = "rtsp://admin:pass@192.168.1.50:554/live"
    assert parse_source(rtsp, "rtsp") == rtsp


def test_parse_source_frozen_mode():
    """Verify parse_source resolves bundled media in PyInstaller frozen mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_meipass = Path(tmpdir)
        media_dir = fake_meipass / "media" / "sample"
        media_dir.mkdir(parents=True, exist_ok=True)
        sample_video = media_dir / "custom_sample.mp4"
        sample_video.write_bytes(b"mock_video_bytes")

        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "_MEIPASS", str(fake_meipass), create=True):
            resolved = parse_source("./media/sample/custom_sample.mp4", "file")
            assert Path(resolved).is_file()
            assert resolved == str(sample_video.resolve())


def test_vicentra_spec_bundles_media():
    """Verify vicentra.spec contains media in datas collection."""
    spec_content = Path("vicentra.spec").read_text(encoding="utf-8")
    assert "('media', 'media')" in spec_content

