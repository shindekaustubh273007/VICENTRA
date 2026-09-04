"""
Phase 6 — Centralized Resource and Runtime Path Resolution.

Distinguishes between:
1. READ-ONLY APPLICATION RESOURCES (bundled static files, default models, templates)
   located via get_resource_path().
2. WRITABLE USER/RUNTIME DATA (SQLite database, application logs, single-instance lock)
   located via get_data_dir() in %LOCALAPPDATA%/VICENTRA.
"""

import os
import sys
from pathlib import Path


def get_base_dir() -> Path:
    """
    Returns the root directory of the application:
    - In frozen/packaged mode: sys._MEIPASS (temporary extraction) or the executable's directory.
    - In development mode: the repository root directory.
    """
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent.resolve()
    
    # Path to repo root: app/core/paths.py -> app/core -> app -> repo root
    return Path(__file__).resolve().parent.parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    Resolves a path to a read-only bundled resource (static assets, bundled models).
    Works consistently in development and packaged PyInstaller distributions.
    """
    return get_base_dir() / relative_path


def get_data_dir() -> Path:
    """
    Returns the writable application directory:
    - On Windows: %LOCALAPPDATA%/VICENTRA
    - Fallback: ~/.vicentra
    Automatically ensures required subdirectories exist (data, logs, runtime, models).
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        data_dir = Path(local_app_data) / "VICENTRA"
    else:
        data_dir = Path.home() / ".vicentra"

    # Ensure required runtime directories exist
    (data_dir / "data").mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(parents=True, exist_ok=True)
    (data_dir / "runtime").mkdir(parents=True, exist_ok=True)
    (data_dir / "models").mkdir(parents=True, exist_ok=True)

    return data_dir


def get_database_url() -> str:
    """
    Returns the SQLite database URL.
    Prefers DATABASE_URL environment variable if set.
    Otherwise defaults to %LOCALAPPDATA%/VICENTRA/data/ibvap.db.
    """
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url

    db_path = get_data_dir() / "data" / "ibvap.db"
    return f"sqlite:///{db_path.as_posix()}"


def get_model_path(model_name_or_path: str) -> str:
    """
    Resolves the model path:
    1. Direct absolute or relative file path if it exists.
    2. Bundled resource (via get_resource_path).
    3. Writable models directory (%LOCALAPPDATA%/VICENTRA/models).
    4. Falls back to original string (e.g. for Ultralytics auto-download).
    """
    # 1. Direct path check
    direct = Path(model_name_or_path)
    if direct.is_file():
        return str(direct.resolve())

    # 2. Bundled resource check
    bundled = get_resource_path(model_name_or_path)
    if bundled.is_file():
        return str(bundled.resolve())

    # 3. User models directory
    user_model = get_data_dir() / "models" / model_name_or_path
    if user_model.is_file():
        return str(user_model.resolve())

    # 4. Fallback to model name
    return model_name_or_path
