@echo off
echo Starting RemScheduler Local Agent...
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
    echo Please create config.ini from config.ini.example
    pause
    exit /b 1
)

:: Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

:: Clear the console for cleaner output
cls

echo ====================================
echo RemScheduler Local Agent v2
echo ====================================
echo.
echo Agent is starting...
echo Press Ctrl+C to stop
echo.

:: Check for database corruption
if exist agent_jobs.db (
    echo Checking database integrity...
    python -c "import sqlite3; conn = sqlite3.connect('agent_jobs.db'); conn.execute('PRAGMA integrity_check'); conn.close()" >nul 2>&1
    if %errorlevel% neq 0 (
        echo Database corruption detected, backing up and recreating...
        if exist agent_jobs.db.backup del agent_jobs.db.backup
        ren agent_jobs.db agent_jobs.db.backup
        echo Old database backed up as agent_jobs.db.backup
    )
)

:: Run the agent
python agent_v2.py

:: If agent exits, pause to see any error messages
if %errorlevel% neq 0 (
    echo.
    echo Agent stopped with error code %errorlevel%
    pause
)