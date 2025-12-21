@echo off
setlocal EnableDelayedExpansion

title Text To BOOK - Portable

echo.
echo ============================================================
echo       Text To BOOK - Portable Launcher
echo ============================================================
echo.

:: Ensure we are running from the script's directory
cd /d "%~dp0"

:: ============================================================
:: 1. Locate Python Environment
:: ============================================================
echo [INFO] Locating Python environment...

set "PYTHON_EXE="

:: Check potential locations
:: Priority 1: .venv root (Conda/Embedded style)
if exist ".venv\python.exe" set "PYTHON_EXE=.venv\python.exe"

:: Priority 2: .venv/Scripts (Standard venv style)
if not defined PYTHON_EXE (
    if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=.venv\Scripts\python.exe"
)

:: Priority 3: venv root
if not defined PYTHON_EXE (
    if exist "venv\python.exe" set "PYTHON_EXE=venv\python.exe"
)

:: Priority 4: venv/Scripts
if not defined PYTHON_EXE (
    if exist "venv\Scripts\python.exe" set "PYTHON_EXE=venv\Scripts\python.exe"
)

if not defined PYTHON_EXE (
    echo [ERROR] Could not find a local Python environment.
    echo.
    echo Please ensure the '.venv' folder is present.
    echo If you haven't set it up yet, run 'setup_cpu.cmd' or 'setup_gpu.cmd'.
    echo.
    pause
    exit /b 1
)

echo [OK] Found Python: %PYTHON_EXE%

:: ============================================================
:: 2. Launch Application
:: ============================================================
echo.
echo [INFO] Starting Text To BOOK...
echo [INFO] Server will be available at http://localhost:8000
echo.

"%PYTHON_EXE%" app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The application stopped with an error (Code: %ERRORLEVEL%).
    echo.
    pause
)

endlocal
