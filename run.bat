@echo off
setlocal
title Text To BOOK

:: Ensure we are in the script directory
cd /d "%~dp0"

:: Check for venv
if not exist ".venv" (
    echo [ERROR] Virtual environment not found.
    echo Please run 'setup.bat' first to install dependencies.
    pause
    exit /b 1
)

:: Activate venv
call .venv\Scripts\activate.bat

:: Launch App
echo Starting Text To BOOK...
python app.py

:: Pause on exit if error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
