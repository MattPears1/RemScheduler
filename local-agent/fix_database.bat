@echo off
echo =================================
echo RemScheduler Database Recovery Tool
echo =================================
echo.
echo This tool will:
echo 1. Stop any running agent processes
echo 2. Fix database corruption issues
echo 3. Recover your pending messages if possible
echo 4. Create a fresh database if needed
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Install psutil if not already installed
echo.
echo Checking dependencies...
python -c "import psutil" 2>nul
if errorlevel 1 (
    echo Installing psutil...
    pip install psutil
)

REM Run the fix
echo.
python fix_database.py

echo.
pause