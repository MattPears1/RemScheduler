#!/usr/bin/env python3
import sqlite3
import os

db_path = 'local_messages.db'

try:
    print(f"Checking database: {db_path}")
    print(f"Database size: {os.path.getsize(db_path)} bytes")
    
    # Try to connect
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check integrity
    result = cursor.execute('PRAGMA integrity_check').fetchone()
    print(f"Integrity check: {result[0]}")
    
    if result[0] != 'ok':
        print("Database is corrupted!")
        
        # Try to recover
        print("\nAttempting recovery...")
        
        # Backup corrupted database
        backup_path = f"{db_path}.corrupted"
        os.rename(db_path, backup_path)
        print(f"Backed up to: {backup_path}")
        
        # Remove WAL and SHM files
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.remove(wal_file)
                print(f"Removed {wal_file}")
        
        print("Database moved. Agent will create a fresh one on next start.")
    else:
        # Check tables
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print(f"\nTables found: {[t[0] for t in tables]}")
        
        # Check pending jobs
        try:
            count = cursor.execute("SELECT COUNT(*) FROM scheduled_jobs WHERE status='PENDING'").fetchone()[0]
            print(f"Pending jobs: {count}")
        except Exception as e:
            print(f"Error checking jobs: {e}")
    
    conn.close()
    
except sqlite3.DatabaseError as e:
    print(f"Database error: {e}")
    print("\nDatabase appears to be corrupted. Backing up...")
    
    # Backup and remove
    if os.path.exists(db_path):
        backup_path = f"{db_path}.corrupted"
        os.rename(db_path, backup_path)
        print(f"Backed up to: {backup_path}")
        
        # Remove WAL and SHM files
        for ext in ['-wal', '-shm']:
            wal_file = db_path + ext
            if os.path.exists(wal_file):
                os.remove(wal_file)
                print(f"Removed {wal_file}")
        
        print("Database removed. Agent will create fresh one on next start.")
        
except Exception as e:
    print(f"Unexpected error: {e}")