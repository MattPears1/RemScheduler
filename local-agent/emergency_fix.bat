@echo off
echo ===================================
echo EMERGENCY DATABASE FIX
echo ===================================
echo.
echo This will forcefully fix the database issue.
echo.
echo Press any key to continue...
pause >nul

echo.
echo Step 1: Killing ALL Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

echo.
echo Step 2: Waiting for processes to terminate...
timeout /t 5 /nobreak

echo.
echo Step 3: Renaming corrupted database...
if exist local_messages.db (
    move /Y local_messages.db local_messages.db.old 2>nul
    if errorlevel 1 (
        echo Failed to rename database. Trying to delete...
        del /F /Q local_messages.db 2>nul
    )
)

echo.
echo Step 4: Removing lock files...
del /F /Q local_messages.db-wal 2>nul
del /F /Q local_messages.db-shm 2>nul
del /F /Q local_messages.db-journal 2>nul

echo.
echo Step 5: Creating fresh database...
echo Database has been reset. The agent will create a new one on startup.
echo.
echo You can now run: run_agent_v2.bat
echo.
pause