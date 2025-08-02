@echo off
echo ================================================
echo       RemScheduler Local Agent V2
echo ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

:: Check if config.ini exists
if not exist config.ini (
    echo ERROR: config.ini not found!
    echo Please create config.ini with your Heroku app URL and credentials
    echo.
    echo Example config.ini:
    echo [server]
    echo url = https://remscheduler-ca6ac87d3a1a.herokuapp.com
    echo.
    echo [auth]
    echo username = your_username
    echo password = your_password
    echo.
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist ".deps_installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo. > .deps_installed
        echo Dependencies installed successfully!
        echo.
    ) else (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

:: Check for database corruption
if exist agent_jobs.db (
    echo Checking database integrity...
    python -c "import sqlite3; try: conn = sqlite3.connect('agent_jobs.db'); conn.execute('PRAGMA integrity_check').fetchone(); conn.close(); exit(0)
except: exit(1)" 2>nul
    if %errorlevel% neq 0 (
        echo Database corruption detected, backing up and recreating...
        if exist agent_jobs.db.backup del agent_jobs.db.backup
        move /Y agent_jobs.db agent_jobs.db.backup 2>nul
        del /F /Q agent_jobs.db-wal 2>nul
        del /F /Q agent_jobs.db-shm 2>nul
        del /F /Q agent_jobs.db-journal 2>nul
        echo Database has been reset.
    )
)

:: Clear the console for cleaner output
cls

echo ================================================
echo       RemScheduler Local Agent V2
echo ================================================
echo.
echo Starting agent...
echo Press Ctrl+C to stop
echo.
echo Connecting to Heroku app...
echo (The app may take 30-60 seconds to wake up)
echo.

:: Run the agent
python agent_v2.py

:: If agent exits, pause to see any error messages
if %errorlevel% neq 0 (
    echo.
    echo Agent stopped with error code %errorlevel%
    pause
) else (
    echo.
    echo Agent stopped normally.
    pause
)