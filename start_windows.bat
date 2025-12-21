@echo off
setlocal EnableDelayedExpansion

title Text To BOOK - Launcher

cd /d "%~dp0"

echo ============================================================
echo       Text To BOOK - Universal Launcher
echo ============================================================
echo.

:: 1. Check Python
set "PYTHON_CMD="
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=python"
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 set "PYTHON_CMD=py"

if not defined PYTHON_CMD (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: 2. Check Virtual Environment
if not exist ".venv" (
    echo [INFO] First time run detected. Setting up environment...
    echo.
    
    :: Create Venv
    "%PYTHON_CMD%" -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    
    :: Upgrade Pip
    .venv\Scripts\python -m pip install --upgrade pip
    
    :: Install Dependencies (Auto-detect GPU)
    echo [INFO] Checking for NVIDIA GPU...
    wmic path win32_VideoController get name | findstr /i "Nvidia" >nul
    if !ERRORLEVEL! EQU 0 (
        echo [INFO] NVIDIA GPU detected. Installing CUDA support...
        .venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
    ) else (
        echo [INFO] No NVIDIA GPU detected. Installing CPU version...
        .venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    )
    
    echo [INFO] Installing requirements...
    .venv\Scripts\pip install -r requirements.txt
    
    echo.
    echo [SUCCESS] Setup complete!
)

:: 3. Check Model (Basic check)
if not exist "models\chatterbox-turbo" (
    echo [WARNING] Model files not found in 'models/chatterbox-turbo'.
    echo If this is a fresh clone, please ensure you have downloaded the model weights.
    echo.
)

:: 4. Run App
echo [INFO] Starting Application...
echo.
.venv\Scripts\python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application crashed.
    pause
)
