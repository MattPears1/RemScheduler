import os
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

# Global state for rate limiting
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

# Import and register blueprints and handlers after app is created
from backend.routes import api_routes
from backend.auth import auth_routes
from backend.websocket_handlers import register_websocket_handlers

app.register_blueprint(api_routes, url_prefix='/api')
app.register_blueprint(auth_routes, url_prefix='/auth')
register_websocket_handlers(socketio)

# Create database tables and default user
with app.app_context():
    from backend.models import User, LocalAgent, Task, ScheduledJob, PresetProfile, SystemStatus
    
    # Drop and recreate tables to handle schema change (removing email field)
    # This is safe for initial deployment
    try:
        db.drop_all()
        logger.info("Dropped existing tables")
    except Exception as e:
        logger.info(f"No existing tables to drop: {e}")
    
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Create default user
    default_user = User(username='matt')
    default_user.set_password('aether2025')  # You can change this password
    db.session.add(default_user)
    db.session.commit()
    logger.info("Default user 'matt' created with password 'aether2025'")

# Initialize the scheduler
from backend.scheduler import init_scheduler
scheduler = init_scheduler(app, socketio)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)