@echo off
echo ================================================
echo       FRESH START - RemScheduler Agent
echo ================================================
echo.
echo This will:
echo 1. Stop all running agents
echo 2. Create a fresh, clean database
echo 3. Start the agent
echo.
echo Press any key to continue...
pause >nul

echo.
echo Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul

echo Waiting...
timeout /t 3 /nobreak >nul

echo.
echo Removing old database files...
del /F /Q local_messages.db* 2>nul
del /F /Q *.db.corrupted.* 2>nul
del /F /Q *.db.old 2>nul

echo.
echo Starting agent with fresh database...
echo.
call run_agent_v2.bat