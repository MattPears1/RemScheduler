from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import secrets
from backend.db import db
from backend.models import User, LocalAgent

auth_routes = Blueprint('auth', __name__)

# Registration removed - single user system

@auth_routes.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.json
        
        # Find user by username
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        login_user(user, remember=True)
        
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username
            }
        })
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@auth_routes.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout current user"""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@auth_routes.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username
    })

@auth_routes.route('/agent-key', methods=['POST'])
@login_required
def generate_agent_key():
    """Generate a new API key for local agent"""
    try:
        data = request.json
        
        # Generate secure API key
        api_key = secrets.token_urlsafe(32)
        
        # Create or update agent
        agent = LocalAgent.query.filter_by(
            user_id=current_user.id,
            name=data['name']
        ).first()
        
        if not agent:
            agent = LocalAgent(
                user_id=current_user.id,
                name=data['name']
            )
        
        agent.set_api_key(api_key)
        db.session.add(agent)
        db.session.commit()
        
        return jsonify({
            'agent_id': agent.id,
            'api_key': api_key,
            'message': 'API key generated successfully. Save this key securely - it cannot be retrieved again.'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to generate API key'}), 500

@auth_routes.route('/agents', methods=['GET'])
@login_required
def get_agents():
    """Get all agents for current user"""
    agents = LocalAgent.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': agent.id,
        'name': agent.name,
        'is_online': agent.is_online,
        'last_seen': agent.last_seen.isoformat() if agent.last_seen else None
    } for agent in agents])