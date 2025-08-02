import os
import logging
from flask import Flask, render_template, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_login import LoginManager
from dotenv import load_dotenv
from datetime import datetime
import jwt

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='dist', static_url_path='')

# Debug OpenAI API key
print(f"[APP INIT] OPENAI_API_KEY present: {bool(os.environ.get('OPENAI_API_KEY'))}")
print(f"[APP INIT] OPENAI_API_KEY length: {len(os.environ.get('OPENAI_API_KEY', ''))}")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aether.db')
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Session configuration for better persistence
app.config['SESSION_COOKIE_NAME'] = 'remscheduler_session'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('ENV') == 'production'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days
app.config['REMEMBER_COOKIE_DURATION'] = 86400 * 30  # 30 days
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('ENV') == 'production'

# Initialize extensions
from backend.db import db
from flask_migrate import Migrate
db.init_app(app)
migrate = Migrate(app, db)
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

# Remove these routes for now - they'll be re-added after blueprints

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

# Catch-all route for React Router - MUST be after all other routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Catch all routes and serve React app"""
    # If it's a file request (has extension), try to serve it
    if '.' in path:
        # Check if file exists in static folder
        if os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        # File not found
        return jsonify({'error': 'Not found'}), 404
    
    # For all other routes, serve the React app
    # This allows React Router to handle client-side routing
    return send_from_directory(app.static_folder, 'index.html')

# Create database tables and default user
with app.app_context():
    from backend.models import User, LocalAgent, Task, ScheduledJob, PresetProfile, SystemStatus
    
    # Create tables if they don't exist (don't drop existing data!)
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Create default user if it doesn't exist
    default_user = User.query.filter_by(username='matt').first()
    if not default_user:
        default_user = User(username='matt')
        default_user.set_password('aether2025')
        db.session.add(default_user)
        db.session.commit()
        logger.info("Default user 'matt' created with password 'aether2025'")
    else:
        logger.info("Default user 'matt' already exists")

# Note: Scheduler removed - now handled by local agent

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
