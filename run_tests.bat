@echo off
echo Running Tests...
REM Activate venv. Quote path just in case.
call ".venv\Scripts\activate.bat"

REM Run pytest using the python from the activated environment
python -m pytest tests/ -v

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ All tests passed!
) else (
    echo.
    echo ❌ Tests failed!
)
