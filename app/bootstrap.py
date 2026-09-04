"""
Phase 6 — Application Bootstrap & Runtime Lifecycle Controller.

Responsibilities:
1. Single-instance enforcement via file lock in %LOCALAPPDATA%/VICENTRA/runtime/
2. Port availability check & intelligent fallback
3. Programmatic Uvicorn server launch
4. Health-check readiness verification before browser launch
5. Automatic default browser opening
6. Graceful shutdown on SIGINT / SIGTERM / Ctrl+C
"""

import os
import sys
import time
import socket
import urllib.request
import urllib.error
import webbrowser
import threading
import signal
from pathlib import Path
from typing import Optional

import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.paths import get_data_dir


class SingleInstanceLock:
    """
    Ensures only one instance of VICENTRA runs at a time.
    If another instance is active, opens the browser to that instance and exits.
    """

    def __init__(self, lock_file: Path):
        self.lock_file = lock_file
        self.acquired = False

    def acquire(self) -> bool:
        if self.lock_file.exists():
            try:
                pid = int(self.lock_file.read_text(encoding="utf-8").strip())
                if self._is_process_running(pid):
                    return False
            except (ValueError, OSError):
                # Stale or corrupted lock file
                pass

        try:
            self.lock_file.write_text(str(os.getpid()), encoding="utf-8")
            self.acquired = True
            return True
        except OSError as e:
            logger.error(f"Cannot write lock file {self.lock_file}: {e}")
            return False

    def release(self):
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except OSError:
                pass
            self.acquired = False

    @staticmethod
    def _is_process_running(pid: int) -> bool:
        """Check if a process with the given PID is currently active on Windows."""
        if os.name == "nt":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            process = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if process:
                kernel32.CloseHandle(process)
                return True
            return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False


def is_port_in_use(host: str, port: int) -> bool:
    """Test whether a TCP port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_available_port(host: str, preferred_port: int, max_attempts: int = 10) -> int:
    """Find preferred_port or the next available port in range."""
    for p in range(preferred_port, preferred_port + max_attempts):
        if not is_port_in_use(host, p):
            return p
    return preferred_port


def wait_for_server_ready(host: str, port: int, timeout: float = 15.0) -> bool:
    """
    Polls /api/health until the server responds HTTP 200 OK.
    """
    url = f"http://{host}:{port}/api/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VICENTRA-Bootstrap"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionRefusedError, socket.timeout):
            time.sleep(0.2)
        except Exception:
            time.sleep(0.2)

    return False


def main() -> int:
    """
    Main application bootstrap entry point.
    """
    # 1. Setup logging
    setup_logging()
    logger.info("=" * 60)
    logger.info("   VICENTRA / IBVAP — Intelligent Border Video Analytics")
    logger.info("=" * 60)
    logger.info("Application launch initiated.")

    # 2. Acquire single instance lock
    lock_file = get_data_dir() / "runtime" / "vicentra.lock"
    lock = SingleInstanceLock(lock_file)
    if not lock.acquire():
        logger.warning("Another instance of VICENTRA is already running.")
        dashboard_url = f"http://{settings.SERVER_HOST}:{settings.SERVER_PORT}/"
        logger.info(f"Opening browser to active instance: {dashboard_url}")
        webbrowser.open(dashboard_url)
        return 0

    # 3. Determine host and port
    host = settings.SERVER_HOST
    preferred_port = settings.SERVER_PORT
    port = find_available_port(host, preferred_port)
    if port != preferred_port:
        logger.warning(f"Preferred port {preferred_port} in use. Using port {port} instead.")

    dashboard_url = f"http://{host}:{port}/"
    logger.info(f"Configured server: {dashboard_url}")

    # 4. Configure Uvicorn server
    config = uvicorn.Config(
        app="app.main:app",
        host=host,
        port=port,
        log_level="info",
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    # 5. Start Uvicorn in background thread
    server_thread = threading.Thread(target=server.run, name="UvicornServer", daemon=True)
    server_thread.start()
    logger.info("Uvicorn server thread started.")

    # 6. Wait for readiness
    logger.info("Waiting for application services to become ready...")
    ready = wait_for_server_ready(host, port, timeout=20.0)
    if not ready:
        logger.error("Server failed to become ready within timeout.")
        lock.release()
        return 1

    logger.info(f"[OK] Backend services ready! Dashboard available at: {dashboard_url}")

    # 7. Open browser automatically
    if settings.AUTO_OPEN_BROWSER:
        logger.info("Opening default browser...")
        try:
            webbrowser.open(dashboard_url)
        except Exception as e:
            logger.warning(f"Could not open browser automatically: {e}")

    # 8. Register signal handlers for clean exit
    stop_event = threading.Event()

    def handle_signal(sig, frame):
        logger.info(f"Received signal {sig}. Initiating graceful shutdown...")
        server.should_exit = True
        stop_event.set()

    try:
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    except (ValueError, AttributeError):
        pass

    # 9. Main loop — wait until server stops
    try:
        while not stop_event.is_set() and server_thread.is_alive():
            stop_event.wait(timeout=1.0)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown requested.")
    finally:
        server.should_exit = True
        server_thread.join(timeout=5.0)
        lock.release()
        logger.info("VICENTRA application shutdown complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
