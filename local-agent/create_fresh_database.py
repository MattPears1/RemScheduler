#!/usr/bin/env python3
"""
Creates a fresh, clean database for RemScheduler Local Agent
"""
import sqlite3
import os
import sys

def create_fresh_database():
    """Create a new database with all required tables"""
    db_path = 'local_messages.db'
    
    # Make absolutely sure no old database exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")
        except Exception as e:
            print(f"Warning: Could not remove old database: {e}")
            print("The file may be locked. Please close all Python processes and try again.")
            return False
    
    # Remove any lock files
    for ext in ['-wal', '-shm', '-journal']:
        lock_file = db_path + ext
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"Removed lock file: {lock_file}")
            except:
                pass
    
    print(f"Creating fresh database: {db_path}")
    
    try:
        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create scheduled_jobs table
        cursor.execute('''
            CREATE TABLE scheduled_jobs (
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
        print("Created scheduled_jobs table")
        
        # Create transcripts table
        cursor.execute('''
            CREATE TABLE transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("Created transcripts table")
        
        # Add indexes for better performance
        cursor.execute('''
            CREATE INDEX idx_scheduled_time ON scheduled_jobs(scheduled_time)
        ''')
        cursor.execute('''
            CREATE INDEX idx_status ON scheduled_jobs(status)
        ''')
        cursor.execute('''
            CREATE INDEX idx_job_group ON scheduled_jobs(job_group_id)
        ''')
        print("Created database indexes")
        
        # Set pragmas for better performance and reliability
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA synchronous=NORMAL')
        cursor.execute('PRAGMA temp_store=MEMORY')
        cursor.execute('PRAGMA mmap_size=30000000000')
        print("Set database pragmas")
        
        conn.commit()
        
        # Verify the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nDatabase created successfully with tables: {[t[0] for t in tables]}")
        
        # Run integrity check
        result = cursor.execute('PRAGMA integrity_check').fetchone()
        if result[0] == 'ok':
            print("Database integrity check: PASSED")
        else:
            print(f"Database integrity check: FAILED - {result[0]}")
            return False
        
        conn.close()
        
        print("\n✓ Fresh database created successfully!")
        print("✓ All tables and indexes are in place")
        print("✓ Database is ready for use")
        
        return True
        
    except Exception as e:
        print(f"\nERROR creating database: {e}")
        return False

if __name__ == '__main__':
    print("=== RemScheduler Fresh Database Creator ===\n")
    
    success = create_fresh_database()
    
    if not success:
        print("\nFailed to create fresh database!")
        print("Please ensure all Python processes are closed and try again.")
        sys.exit(1)
    
    print("\nYou can now start the agent with: run_agent_v2.bat")