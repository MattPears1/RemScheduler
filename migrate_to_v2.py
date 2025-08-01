"""
Migration script to switch to V2 architecture
This updates the app to use the new routes and WebSocket handlers
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of the file"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"Backed up {filepath} to {backup_path}")

def update_app_py():
    """Update app.py to use V2 handlers"""
    app_content = '''import os
import logging
from flask import Flask, render_template, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_login import LoginManager
from dotenv import load_dotenv
from datetime import datetime
import jwt

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aether.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from backend.db import db
db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
login_manager = LoginManager(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for rate limiting (kept for compatibility)
system_state = {
    'rate_limited': False,
    'reset_time': None
}

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@login_manager.user_loader
def load_user(user_id):
    from backend.models import User
    return User.query.get(int(user_id))

# Import and register V2 blueprints and handlers
from backend.routes_v2 import api_routes_v2
from backend.auth import auth_routes
from backend.websocket_handlers_v2 import register_websocket_handlers_v2

app.register_blueprint(api_routes_v2, url_prefix='/api')
app.register_blueprint(auth_routes, url_prefix='/auth')
register_websocket_handlers_v2(socketio)

# Create database tables and default user
with app.app_context():
    from backend.models import User, LocalAgent, Task, ScheduledJob, PresetProfile, SystemStatus
    
    # Drop old tables (they're now managed by the agent)
    try:
        db.drop_all()
        logger.info("Dropped existing tables")
    except Exception as e:
        logger.info(f"No existing tables to drop: {e}")
    
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Create default user
    default_user = User(username='matt')
    default_user.set_password('aether2025')
    db.session.add(default_user)
    db.session.commit()
    logger.info("Default user 'matt' created with password 'aether2025'")

# Note: Scheduler removed - now handled by local agent

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
'''
    
    backup_file('app.py')
    with open('app.py', 'w') as f:
        f.write(app_content)
    print("Updated app.py to use V2 architecture")

def update_frontend():
    """Update frontend JavaScript to work with V2 API"""
    js_update = '''
// Add this to app.js after the socket connection setup

// Notify server we're a web client
state.socket.on('connect', () => {
    console.log('Connected to server');
    state.socket.emit('web_connect');
});

// Handle job updates from agent
state.socket.on('jobs_updated', (data) => {
    if (state.currentScreen === 'mission-control') {
        displayJobGroups(data.job_groups);
    }
});

// Handle transcript updates from agent
state.socket.on('transcripts_updated', (data) => {
    if (state.currentScreen === 'saved-messages') {
        displaySavedMessages(data.transcripts);
    }
});

// Handle schedule confirmations
state.socket.on('schedule_confirmed', (data) => {
    alert(`Successfully scheduled ${data.jobs_created} jobs!`);
    showScreen('dashboard');
    document.getElementById('task-text').value = '';
    document.getElementById('proceed-schedule').disabled = true;
});

state.socket.on('schedule_failed', (data) => {
    alert(`Failed to schedule: ${data.error}`);
});
'''
    
    print("\nAdd the following to static/js/app.js:")
    print(js_update)

def create_run_v2_script():
    """Create script to run V2 agent"""
    script_content = '''@echo off
echo Starting RemScheduler Local Agent V2...
echo.
echo This version stores all data locally and manages scheduling independently.
echo Press Ctrl+C to stop.
echo.

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

REM Run the V2 agent
echo Starting agent V2...
python agent_v2.py

REM If the agent exits, pause so user can see any error messages
echo.
echo Agent stopped.
pause
'''
    
    with open('local-agent/run_agent_v2.bat', 'w') as f:
        f.write(script_content)
    print("Created local-agent/run_agent_v2.bat")

def main():
    print("=== RemScheduler V2 Migration ===")
    print("This will update the system to store everything locally in the agent")
    print()
    
    # Update app.py
    update_app_py()
    
    # Create V2 run script
    create_run_v2_script()
    
    # Show frontend update instructions
    update_frontend()
    
    print("\n=== Migration Complete ===")
    print("\nNext steps:")
    print("1. Deploy the updated app.py to Heroku")
    print("2. Update static/js/app.js with the provided code")
    print("3. Stop the old agent and run: local-agent/run_agent_v2.bat")
    print("\nThe new agent will:")
    print("- Store all messages and schedules locally in SQLite")
    print("- Manage all scheduling independently")
    print("- Continue working even if Heroku is down")
    print("- Sync with the web interface when connected")

if __name__ == '__main__':
    main()