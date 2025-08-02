@echo off
echo ================================================
echo       RemScheduler Local Agent V2
echo ================================================
echo.

REM Kill any existing Python processes that might be using the database
echo Checking for running Python processes...
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python"') do (
    echo Stopping process %%i...
    taskkill /PID %%i /F 2>nul
)

REM Wait a moment for processes to fully terminate
timeout /t 2 /nobreak >nul

REM Check if database exists and if it's corrupted
if exist local_messages.db (
    echo Checking database integrity...
    python -c "import sqlite3; conn = sqlite3.connect('local_messages.db'); conn.execute('PRAGMA quick_check').fetchone(); conn.close(); print('Database OK')" 2>nul
    if errorlevel 1 (
        echo Database appears to be corrupted. Creating backup and starting fresh...
        move /Y local_messages.db local_messages.db.backup 2>nul
        del /F /Q local_messages.db-wal 2>nul
        del /F /Q local_messages.db-shm 2>nul
        del /F /Q local_messages.db-journal 2>nul
        echo Database has been reset.
    )
)

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

REM Run the agent
echo.
echo Starting RemScheduler Local Agent...
echo Press Ctrl+C to stop
echo.
python agent_v2.py

REM If the agent exits, show any error and pause
echo.
echo Agent stopped.
pause