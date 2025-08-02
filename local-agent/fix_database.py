#!/usr/bin/env python3
"""
Database recovery utility for RemScheduler Local Agent
Handles database corruption and locked file issues
"""
import os
import sqlite3
import shutil
import time
import psutil
import sys

def kill_python_processes():
    """Kill any Python processes that might be locking the database"""
    print("Checking for running Python processes...")
    killed = False
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if it's a Python process running agent_v2.py
                if proc.info['name'] in ['python.exe', 'python', 'pythonw.exe']:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and any('agent_v2.py' in arg for arg in cmdline):
                        print(f"Found agent process (PID: {proc.info['pid']}), terminating...")
                        proc.terminate()
                        killed = True
                        time.sleep(1)  # Give it time to terminate
                        
                        # Force kill if still running
                        if proc.is_running():
                            proc.kill()
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
    except Exception as e:
        print(f"Error checking processes: {e}")
    
    if killed:
        print("Waiting for processes to fully terminate...")
        time.sleep(3)
    else:
        print("No agent processes found running.")
    
    return killed

def remove_lock_files(db_path):
    """Remove SQLite lock files"""
    removed = False
    for ext in ['-wal', '-shm', '-journal']:
        lock_file = db_path + ext
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"Removed lock file: {lock_file}")
                removed = True
            except Exception as e:
                print(f"Warning: Could not remove {lock_file}: {e}")
    return removed

def check_database_integrity(db_path):
    """Check if database is corrupted"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        result = cursor.execute('PRAGMA integrity_check').fetchone()
        conn.close()
        return result[0] == 'ok'
    except Exception as e:
        print(f"Database check failed: {e}")
        return False

def backup_database(db_path):
    """Create a backup of the database"""
    timestamp = int(time.time())
    backup_path = f"{db_path}.backup.{timestamp}"
    
    try:
        shutil.copy2(db_path, backup_path)
        print(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Backup failed: {e}")
        return None

def recover_data_from_corrupted(corrupted_path):
    """Try to recover data from corrupted database"""
    recovered_jobs = []
    recovered_transcripts = []
    
    try:
        # Use read-only mode to avoid locking
        conn = sqlite3.connect(f'file:{corrupted_path}?mode=ro', uri=True)
        cursor = conn.cursor()
        
        # Try to recover scheduled jobs
        try:
            cursor.execute("SELECT * FROM scheduled_jobs WHERE status = 'PENDING'")
            recovered_jobs = cursor.fetchall()
            print(f"Recovered {len(recovered_jobs)} pending jobs")
        except:
            print("Could not recover jobs")
        
        # Try to recover transcripts
        try:
            cursor.execute("SELECT * FROM transcripts")
            recovered_transcripts = cursor.fetchall()
            print(f"Recovered {len(recovered_transcripts)} transcripts")
        except:
            print("Could not recover transcripts")
        
        conn.close()
        
    except Exception as e:
        print(f"Recovery attempt failed: {e}")
    
    return recovered_jobs, recovered_transcripts

def create_fresh_database(db_path, recovered_data=None):
    """Create a fresh database with recovered data if available"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_group_id TEXT NOT NULL,
            message_text TEXT NOT NULL,
            scheduled_time TIMESTAMP NOT NULL,
            target_hwnd INTEGER NOT NULL,
            target_title TEXT,
            status TEXT DEFAULT 'PENDING',
            executed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert recovered data if available
    if recovered_data:
        jobs, transcripts = recovered_data
        
        if jobs:
            print(f"Restoring {len(jobs)} pending jobs...")
            for job in jobs:
                try:
                    cursor.execute('''
                        INSERT INTO scheduled_jobs 
                        (job_group_id, message_text, scheduled_time, target_hwnd, 
                         target_title, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (job[1], job[2], job[3], job[4], job[5], 'PENDING', job[8]))
                except Exception as e:
                    print(f"Failed to restore job: {e}")
        
        if transcripts:
            print(f"Restoring {len(transcripts)} transcripts...")
            for transcript in transcripts:
                try:
                    cursor.execute('''
                        INSERT INTO transcripts (text, created_at)
                        VALUES (?, ?)
                    ''', (transcript[1], transcript[2]))
                except Exception as e:
                    print(f"Failed to restore transcript: {e}")
    
    conn.commit()
    conn.close()
    print("Fresh database created successfully!")

def main():
    db_path = 'local_messages.db'
    
    print("=== RemScheduler Database Recovery Tool ===\n")
    
    # Step 1: Kill any running agent processes
    kill_python_processes()
    
    # Step 2: Remove lock files
    print("\nRemoving lock files...")
    remove_lock_files(db_path)
    
    # Step 3: Check if database exists and is corrupted
    if os.path.exists(db_path):
        print(f"\nChecking database integrity...")
        is_healthy = check_database_integrity(db_path)
        
        if is_healthy:
            print("Database is healthy! No recovery needed.")
            
            # Still remove lock files just in case
            remove_lock_files(db_path)
            
            print("\nYou can now start the agent normally.")
            return
        
        print("Database is corrupted. Starting recovery process...")
        
        # Step 4: Try to recover data
        print("\nAttempting data recovery...")
        recovered_data = recover_data_from_corrupted(db_path)
        
        # Step 5: Backup corrupted database
        print("\nBacking up corrupted database...")
        backup_path = backup_database(db_path)
        
        # Step 6: Remove corrupted database
        try:
            os.remove(db_path)
            print(f"Removed corrupted database: {db_path}")
        except Exception as e:
            print(f"Error removing corrupted database: {e}")
            print("Please manually delete the file and run this script again.")
            return
        
        # Step 7: Remove any remaining lock files
        remove_lock_files(db_path)
        
        # Step 8: Create fresh database with recovered data
        print("\nCreating fresh database...")
        create_fresh_database(db_path, recovered_data)
        
    else:
        print("No database found. Creating fresh database...")
        create_fresh_database(db_path)
    
    print("\n=== Recovery Complete! ===")
    print("You can now start the agent using run_agent_v2.bat")
    print("\nNote: Some data may have been lost if the corruption was severe.")
    print(f"A backup of the old database (if any) is saved as: {backup_path if 'backup_path' in locals() else 'N/A'}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        print("Please report this error.")
    
    input("\nPress Enter to exit...")