from flask_socketio import emit, disconnect
from flask import request, current_app
from datetime import datetime
from backend.db import db
from backend.models import LocalAgent

# Connected agents storage
connected_agents = {}
agent_windows = {}
agent_jobs = {}
agent_transcripts = {}

def register_websocket_handlers_v2(socketio):
    """Register WebSocket event handlers for V2 architecture"""
    
    @socketio.on('agent_auth')
    def handle_agent_auth(data):
        """Authenticate local agent connection"""
        try:
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                emit('auth_error', {'error': 'Username and password required'})
                disconnect()
                return
            
            # Authenticate user
            from backend.models import User
            user = User.query.filter_by(username=username).first()
            
            if not user or not user.check_password(password):
                emit('auth_error', {'error': 'Invalid credentials'})
                disconnect()
                return
            
            # Create or get agent for this user
            agent = LocalAgent.query.filter_by(user_id=user.id).first()
            if not agent:
                agent = LocalAgent(
                    user_id=user.id,
                    name='Desktop Agent',
                    api_key_hash='not_used'
                )
                db.session.add(agent)
                db.session.commit()
            
            # Update agent status
            agent.is_online = True
            agent.last_seen = datetime.utcnow()
            db.session.commit()
            
            # Store connection
            connected_agents[request.sid] = agent
            agent_windows[agent.id] = []
            
            emit('auth_success', {'agent_id': agent.id})
            current_app.logger.info(f"Agent {agent.name} connected")
            
            # Notify all web clients that agent is online
            socketio.emit('agent_connected', {
                'agent_id': agent.id,
                'agent_name': agent.name
            }, room=None)
            
        except Exception as e:
            current_app.logger.error(f"Agent auth error: {str(e)}")
            emit('auth_error', {'error': 'Authentication failed'})
            disconnect()
    
    @socketio.on('agent_sends_window_list')
    def handle_window_list(data):
        """Receive window list from agent"""
        try:
            if request.sid not in connected_agents:
                emit('error', {'error': 'Not authenticated'})
                return
            
            agent = connected_agents[request.sid]
            windows = data.get('windows', [])
            
            # Store windows for this agent
            agent_windows[agent.id] = windows
            
            # Broadcast to all connected clients
            socketio.emit('windows_updated', {
                'agent_id': agent.id,
                'windows': windows
            }, room=None)
            
            current_app.logger.info(f"Received {len(windows)} windows from agent {agent.name}")
            
        except Exception as e:
            current_app.logger.error(f"Window list error: {str(e)}")
    
    @socketio.on('agent_jobs_status')
    def handle_jobs_status(data):
        """Receive job status from agent"""
        try:
            if request.sid not in connected_agents:
                return
            
            agent = connected_agents[request.sid]
            job_groups = data.get('job_groups', [])
            
            # Store jobs for this agent
            agent_jobs[agent.id] = job_groups
            
            # Broadcast to all connected web clients
            socketio.emit('jobs_updated', {
                'agent_id': agent.id,
                'job_groups': job_groups
            }, room=None)
            
            current_app.logger.info(f"Received job status from agent {agent.name}")
            
        except Exception as e:
            current_app.logger.error(f"Jobs status error: {str(e)}")
    
    @socketio.on('agent_transcripts')
    def handle_transcripts(data):
        """Receive transcripts from agent"""
        try:
            if request.sid not in connected_agents:
                return
            
            agent = connected_agents[request.sid]
            transcripts = data.get('transcripts', [])
            
            # Store transcripts for this agent
            agent_transcripts[agent.id] = transcripts
            
            # Broadcast to all connected web clients
            socketio.emit('transcripts_updated', {
                'agent_id': agent.id,
                'transcripts': transcripts
            }, room=None)
            
            current_app.logger.info(f"Received transcripts from agent {agent.name}")
            
        except Exception as e:
            current_app.logger.error(f"Transcripts error: {str(e)}")
    
    @socketio.on('schedule_success')
    def handle_schedule_success(data):
        """Handle schedule success from agent"""
        if request.sid not in connected_agents:
            return
        
        # Broadcast to web clients
        socketio.emit('schedule_confirmed', data, room=None)
        current_app.logger.info(f"Schedule confirmed: {data}")
    
    @socketio.on('schedule_error')
    def handle_schedule_error(data):
        """Handle schedule error from agent"""
        if request.sid not in connected_agents:
            return
        
        # Broadcast to web clients
        socketio.emit('schedule_failed', data, room=None)
        current_app.logger.error(f"Schedule failed: {data}")
    
    @socketio.on('job_complete')
    def handle_job_complete(data):
        """Handle job completion from agent"""
        if request.sid not in connected_agents:
            return
        
        # Broadcast to web clients
        socketio.emit('job_status_updated', {
            'job_id': data['job_id'],
            'status': 'SENT'
        }, room=None)
        
        current_app.logger.info(f"Job {data['job_id']} completed")
    
    @socketio.on('job_failed')
    def handle_job_failed(data):
        """Handle job failure from agent"""
        if request.sid not in connected_agents:
            return
        
        # Broadcast to web clients
        socketio.emit('job_status_updated', {
            'job_id': data['job_id'],
            'status': 'FAILED',
            'error': data.get('reason', 'Unknown error')
        }, room=None)
        
        current_app.logger.error(f"Job {data['job_id']} failed: {data.get('reason')}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle agent disconnection"""
        try:
            if request.sid in connected_agents:
                agent = connected_agents[request.sid]
                agent.is_online = False
                agent.last_seen = datetime.utcnow()
                db.session.commit()
                
                # Clean up
                del connected_agents[request.sid]
                if agent.id in agent_windows:
                    del agent_windows[agent.id]
                if agent.id in agent_jobs:
                    del agent_jobs[agent.id]
                if agent.id in agent_transcripts:
                    del agent_transcripts[agent.id]
                
                # Notify clients
                socketio.emit('agent_disconnected', {'agent_id': agent.id})
                
                current_app.logger.info(f"Agent {agent.name} disconnected")
                
        except Exception as e:
            current_app.logger.error(f"Disconnect error: {str(e)}")
    
    # Web client events
    @socketio.on('web_connect')
    def handle_web_connect():
        """Handle web client connection"""
        current_app.logger.info(f"Web client connected: {request.sid}")
        
        # Send agent connection status
        if connected_agents:
            for sid, agent in connected_agents.items():
                emit('agent_connected', {
                    'agent_id': agent.id,
                    'agent_name': agent.name
                })
        
        # Send current state to web client
        for agent_id, windows in agent_windows.items():
            emit('windows_updated', {
                'agent_id': agent_id,
                'windows': windows
            })
        
        for agent_id, job_groups in agent_jobs.items():
            emit('jobs_updated', {
                'agent_id': agent_id,
                'job_groups': job_groups
            })
        
        for agent_id, transcripts in agent_transcripts.items():
            emit('transcripts_updated', {
                'agent_id': agent_id,
                'transcripts': transcripts
            })
    
    return socketio