@echo off
echo ================================================
echo    COMPLETE DATABASE RESET FOR REMSCHEDULER
echo ================================================
echo.
echo This will completely reset your database and remove ALL:
echo - Pending messages
echo - Message history  
echo - Saved transcripts
echo.
echo Press Ctrl+C now if you want to cancel...
echo Otherwise, press any key to continue with the reset.
pause >nul

echo.
echo Step 1: Forcefully killing ALL Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM py.exe 2>nul

echo.
echo Step 2: Waiting for processes to fully terminate...
timeout /t 5 /nobreak

echo.
echo Step 3: Creating backup folder for old database files...
if not exist "database_backup" mkdir database_backup

echo.
echo Step 4: Moving old database files to backup folder...
if exist local_messages.db (
    echo Moving local_messages.db to backup folder...
    move /Y local_messages.db database_backup\local_messages_backup_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%.db 2>nul
    if exist local_messages.db (
        echo Failed to move, forcing deletion...
        del /F /Q local_messages.db
    )
)

echo.
echo Step 5: Removing ALL database-related files...
del /F /Q local_messages.db 2>nul
del /F /Q local_messages.db-wal 2>nul
del /F /Q local_messages.db-shm 2>nul
del /F /Q local_messages.db-journal 2>nul
del /F /Q *.db.corrupted.* 2>nul
del /F /Q *.db.old 2>nul

echo.
echo Step 6: Creating fresh database structure...
python create_fresh_database.py

echo.
echo ================================================
echo    DATABASE RESET COMPLETE!
echo ================================================
echo.
echo Your database has been completely reset.
echo All old data has been moved to the 'database_backup' folder.
echo.
echo You can now run: run_agent_v2.bat
echo.
pause