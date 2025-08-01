@echo off
echo Starting RemScheduler Local Agent...
echo.
echo This agent will connect to your Heroku app and monitor command prompt windows.
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
if not exist ".deps_installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 0 (
        echo. > .deps_installed
        echo Dependencies installed successfully!
        echo.
    ) else (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Run the agent
echo Starting agent...
python agent.py

REM If the agent exits, pause so user can see any error messages
echo.
echo Agent stopped.
pause