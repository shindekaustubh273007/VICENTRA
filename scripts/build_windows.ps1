# VICENTRA / IBVAP - Windows Packaging Build Script

$ErrorActionPreference = 'Stop'

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host '   VICENTRA / IBVAP - Windows Build Process' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

$PythonPath = '.\.venv\Scripts\python.exe'
if (-not (Test-Path $PythonPath)) {
    $PythonPath = 'python'
}

Write-Host ''
Write-Host '[1/5] Checking environment...' -ForegroundColor Yellow
& $PythonPath --version

Write-Host ''
Write-Host '[2/5] Checking PyInstaller installation...' -ForegroundColor Yellow
$PyInstallerInstalled = & $PythonPath -m pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host 'Installing PyInstaller...' -ForegroundColor Yellow
    & $PythonPath -m pip install pyinstaller
} else {
    Write-Host 'PyInstaller is already installed.' -ForegroundColor Green
}

Write-Host ''
Write-Host '[3/5] Cleaning previous build folders...' -ForegroundColor Yellow
if (Test-Path 'build') {
    Remove-Item -Recurse -Force 'build'
}
if (Test-Path 'dist\VICENTRA') {
    Remove-Item -Recurse -Force 'dist\VICENTRA'
}

Write-Host ''
Write-Host '[4/5] Running PyInstaller build...' -ForegroundColor Yellow
& $PythonPath -m PyInstaller --clean vicentra.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ''
    Write-Host '[ERROR] PyInstaller build failed!' -ForegroundColor Red
    exit 1
}

Write-Host ''
Write-Host '[5/5] Verifying distribution...' -ForegroundColor Yellow
$ExePath = 'dist\VICENTRA\VICENTRA.exe'
# PyInstaller v6+ places bundled datas inside _internal/ subdirectory
$StaticPath = 'dist\VICENTRA\_internal\static'
$ModelPath = 'dist\VICENTRA\_internal\yolov8n.pt'

$AllValid = $true
if (Test-Path $ExePath) {
    Write-Host "  [OK] Executable generated: $ExePath" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Missing $ExePath" -ForegroundColor Red
    $AllValid = $false
}

if (Test-Path $StaticPath) {
    Write-Host "  [OK] Static assets bundled: $StaticPath" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Missing $StaticPath" -ForegroundColor Red
    $AllValid = $false
}

if (Test-Path $ModelPath) {
    Write-Host "  [OK] Model weights bundled: $ModelPath" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Missing $ModelPath" -ForegroundColor Red
    $AllValid = $false
}

if ($AllValid) {
    Write-Host ''
    Write-Host '==========================================================' -ForegroundColor Green
    Write-Host '   BUILD SUCCESSFUL!' -ForegroundColor Green
    Write-Host '   Distribution folder: dist/VICENTRA' -ForegroundColor Green
    Write-Host '   Launch command:      .\dist\VICENTRA\VICENTRA.exe' -ForegroundColor Green
    Write-Host '==========================================================' -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host '[FAIL] Build finished with missing assets.' -ForegroundColor Red
    exit 1
}
