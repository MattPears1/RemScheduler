@echo off
echo Stopping any running agents...
taskkill /F /IM python.exe 2>nul
echo.
echo Waiting for processes to terminate...
timeout /t 3 /nobreak >nul
echo.
echo Starting RemScheduler Local Agent V2...
echo.
echo This version stores all data locally and manages scheduling independently.
echo Press Ctrl+C to stop.
echo.

REM Run the V2 agent
call run_agent_v2.bat