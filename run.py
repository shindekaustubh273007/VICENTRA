import sys
import os
import subprocess
from pathlib import Path

# Auto-switch to virtual environment if running with system python
if sys.prefix == sys.base_prefix:
    venv_python = Path(__file__).parent / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists() and sys.executable.lower() != str(venv_python).lower():
        sys.exit(subprocess.call([str(venv_python)] + sys.argv))

if __name__ == "__main__":
    if "--dev" in sys.argv or "--reload" in sys.argv:
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    else:
        from app.bootstrap import main
        sys.exit(main())

