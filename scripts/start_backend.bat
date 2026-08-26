@echo off
echo Starting Jarvis Backend...
echo.

cd /d "%~dp0.."

if not exist "backend\.venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Run: python -m venv backend\.venv
    echo Then: backend\.venv\Scripts\pip.exe install -r backend\requirements.txt
    pause
    exit /b 1
)

echo Using Python: backend\.venv\Scripts\python.exe
echo.

backend\.venv\Scripts\python.exe -m backend.api.main
