"""
VICENTRA / IBVAP — Main Application Launcher.

Entry point for PyInstaller executable packaging.
Launches the bootstrap controller, starts the backend, verifies readiness,
and opens the default browser to the command dashboard.
"""

import sys
from app.bootstrap import main

if __name__ == "__main__":
    sys.exit(main())
