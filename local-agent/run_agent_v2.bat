@echo off
echo Starting RemScheduler Local Agent V2...
echo.
echo This version stores all data locally and manages scheduling independently.
echo Press Ctrl+C to stop.
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist ".deps_installed_v2" (
    echo Installing dependencies...
    pip install -r requirements-windows.txt
    pip install apscheduler
    if errorlevel 0 (
        echo. > .deps_installed_v2
        echo Dependencies installed successfully!
        echo.
    ) else (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the V2 agent
echo Starting agent V2...
python agent_v2.py

REM If the agent exits, pause so user can see any error messages
echo.
echo Agent stopped.
pause
