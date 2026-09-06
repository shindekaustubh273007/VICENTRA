@echo off
echo ============================================================
echo    VICENTRA / IBVAP — One-Click Project Setup (Windows)
echo ============================================================
echo.

:: Step 1: Create virtual environment
echo [1/3] Creating Python virtual environment (.venv)...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment. Is Python installed and on PATH?
    pause
    exit /b 1
)

:: Step 2: Install Python dependencies
echo [2/3] Installing Python dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

:: Step 3: Setup environment file
echo [3/3] Setting up environment configuration...
if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo       Created .env from .env.example
    ) else (
        echo       No .env.example found, skipping .env creation.
    )
) else (
    echo       .env already exists, skipping.
)

echo.
echo ============================================================
echo    Setup complete!
echo.
echo    To start VICENTRA, run:
echo        python run.py
echo.
echo    Dashboard will open at: http://localhost:8000
echo ============================================================
pause
