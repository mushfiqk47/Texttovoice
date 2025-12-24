@echo off
setlocal EnableDelayedExpansion
title Text To BOOK - Setup

echo.
echo ============================================================
echo       Text To BOOK - First Time Setup
echo ============================================================
echo.

:: 1. Locate compatible Python
set "PYTHON_CMD=python"

echo [INFO] Checking for compatible Python versions...

:: Check for py launcher availability and prefer 3.11 > 3.10 > 3.12
:: (3.12 is newer/stricter, 3.11 is golden standard for ML right now)

py -3.11 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3.11"
    goto :FoundPy
)

py -3.10 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3.10"
    goto :FoundPy
)

py -3.12 --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=py -3.12"
    goto :FoundPy
)

:: Fallback to default python
python --version >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
    goto :FoundPy
)

echo [ERROR] Python is not installed or not in your PATH.
echo Please install Python 3.10 or newer.
pause
exit /b 1

:FoundPy
echo [INFO] Using Python command: !PYTHON_CMD!
!PYTHON_CMD! --version
echo.
echo [WARNING] Ensure you are using Python 3.10, 3.11, or 3.12.
echo Newer versions (like 3.14) might not support PyTorch yet.
echo.
timeout /t 3


:: 2. Create Virtual Environment
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    !PYTHON_CMD! -m venv .venv
    if !ERRORLEVEL! NEQ 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [INFO] Virtual environment already exists.
)

:: 3. Activate Virtual Environment
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

:: 4. Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

:: 5. Install Dependencies & Hardware Selection
echo.
echo ============================================================
echo                Hardware Selection
echo ============================================================
echo 1. I have an NVIDIA GPU (Faster generation)
echo 2. I do not have a GPU / I want to use CPU (Slower, compatible with all PCs)
echo.
set /p choice="Enter your choice (1 or 2): "

echo.
echo [INFO] Installing project requirements first...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

if "%choice%"=="1" (
    echo.
    echo [INFO] Enforcing CUDA 12.1 PyTorch installation...
    :: Force reinstall to ensure we have the GPU version, overwriting any CPU version from requirements
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 --force-reinstall
) else (
    echo.
    echo [INFO] Ensuring CPU PyTorch installation...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu --force-reinstall
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] PyTorch installation failed.
    echo.
    pause
    exit /b 1
)

:: 7. Success
echo.
echo ============================================================
echo                 Setup Complete!
echo ============================================================
echo.
echo You can now run the application using 'run.bat'.
echo.
echo Press any key to exit...
pause >nul
