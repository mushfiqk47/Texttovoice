# Contributing to Text To BOOK

## Setup
1. Run `setup.bat` to initialize environment.
2. Activate venv: `.venv\Scripts\activate`.

## Running Tests
Run the included batch script:
```powershell
.\run_tests.bat
```
Or manually:
```bash
pytest tests/ -v
```

## Structure
- `backend/`: FastAPI application
  - `routers/`: API endpoints
  - `services.py`: Core logic (TTS)
  - `rate_limit.py`: Custom rate limiter
- `frontend/`: Vanilla JS UI
- `models/`: Local model storage

## Coding Standards
- Use `black` for formatting if possible.
- Add type hints to all new functions.
- Ensure `requirements.txt` is up to date.
