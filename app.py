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

@app.route('/')
def index():
    """Serve the main application page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

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
