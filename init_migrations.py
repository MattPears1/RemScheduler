#!/usr/bin/env python3
"""
Initialize database migrations for RemScheduler.
Run this script to set up Flask-Migrate for the first time.
"""

import os
import sys
from flask_migrate import init, migrate, upgrade
from app import app, db

def init_db_migrations():
    """Initialize database migrations"""
    with app.app_context():
        # Check if migrations folder exists
        migrations_path = os.path.join(os.path.dirname(__file__), 'migrations')
        
        if not os.path.exists(migrations_path):
            print("Initializing database migrations...")
            init()
            print("✓ Migrations initialized")
        else:
            print("⚠ Migrations folder already exists")
        
        # Create initial migration
        print("\nCreating initial migration...")
        try:
            migrate(message='Initial migration')
            print("✓ Initial migration created")
        except Exception as e:
            print(f"⚠ Migration already exists or error: {e}")
        
        # Apply migrations
        print("\nApplying migrations...")
        upgrade()
        print("✓ Database schema updated")
        
        # Show current tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\nCurrent database tables: {', '.join(tables)}")

if __name__ == '__main__':
    init_db_migrations()