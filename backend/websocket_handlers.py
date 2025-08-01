from flask_socketio import emit, disconnect
from flask import request, current_app
from datetime import datetime, timedelta
import jwt
from backend.db import db
from backend.models import LocalAgent, SystemStatus, ScheduledJob

# Connected agents storage
connected_agents = {}
agent_windows = {}

def register_websocket_handlers(socketio):
    """Register all WebSocket event handlers"""
    
    @socketio.on('agent_auth')
    def handle_agent_auth(data):
        """Authenticate local agent connection"""
        try:
            api_key = data.get('api_key')
            if not api_key:
                emit('auth_error', {'error': 'No API key provided'})
                disconnect()
                return
            
            # Find agent by checking API key
            agent = None
            for a in LocalAgent.query.all():
                if a.check_api_key(api_key):
                    agent = a
                    break
            
            if not agent:
                emit('auth_error', {'error': 'Invalid API key'})
                disconnect()
                return
            
            # Update agent status
            agent.is_online = True
            agent.last_seen = datetime.utcnow()
            db.session.commit()
            
            # Store connection
            connected_agents[request.sid] = agent
            agent_windows[agent.id] = []
            
            emit('auth_success', {'agent_id': agent.id})
            current_app.logger.info(f"Agent {agent.name} connected")
            
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
    
    @socketio.on('global_rate_limit_detected')
    def handle_rate_limit(data):
        """Handle global rate limit detection"""
        try:
            if request.sid not in connected_agents:
                emit('error', {'error': 'Not authenticated'})
                return
            
            reset_time = datetime.fromisoformat(data['reset_utc'])
            
            # Update system status
            system_status = SystemStatus.get_current_status()
            system_status.rate_limited = True
            system_status.reset_time = reset_time
            system_status.last_updated = datetime.utcnow()
            db.session.commit()
            
            # Calculate postponement delta
            now = datetime.utcnow()
            if reset_time > now:
                delta = reset_time - now
                
                # Update all pending jobs
                pending_jobs = ScheduledJob.query.filter(
                    ScheduledJob.status == 'PENDING',
                    ScheduledJob.scheduled_time < reset_time
                ).all()
                
                for job in pending_jobs:
                    job.scheduled_time = reset_time + (job.scheduled_time - now)
                
                db.session.commit()
                
                current_app.logger.info(f"Rate limit detected. Postponed {len(pending_jobs)} jobs until {reset_time}")
                
                # Notify all clients
                socketio.emit('rate_limit_active', {
                    'reset_time': reset_time.isoformat(),
                    'jobs_postponed': len(pending_jobs)
                })
            
        except Exception as e:
            current_app.logger.error(f"Rate limit handling error: {str(e)}")
    
    @socketio.on('job_complete')
    def handle_job_complete(data):
        """Handle job completion notification from agent"""
        try:
            if request.sid not in connected_agents:
                emit('error', {'error': 'Not authenticated'})
                return
            
            job_id = data.get('job_id')
            job = ScheduledJob.query.get(job_id)
            
            if job:
                job.status = 'SENT'
                job.executed_at = datetime.utcnow()
                db.session.commit()
                
                # Notify clients
                socketio.emit('job_status_updated', {
                    'job_id': job_id,
                    'status': 'SENT'
                })
                
                current_app.logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            current_app.logger.error(f"Job complete error: {str(e)}")
    
    @socketio.on('job_failed')
    def handle_job_failed(data):
        """Handle job failure notification from agent"""
        try:
            if request.sid not in connected_agents:
                emit('error', {'error': 'Not authenticated'})
                return
            
            job_id = data.get('job_id')
            reason = data.get('reason', 'Unknown error')
            
            job = ScheduledJob.query.get(job_id)
            if job:
                job.status = 'FAILED'
                job.error_message = reason
                db.session.commit()
                
                # Notify clients
                socketio.emit('job_status_updated', {
                    'job_id': job_id,
                    'status': 'FAILED',
                    'error': reason
                })
                
                current_app.logger.error(f"Job {job_id} failed: {reason}")
            
        except Exception as e:
            current_app.logger.error(f"Job failed error: {str(e)}")
    
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
                
                # Notify clients
                socketio.emit('agent_disconnected', {'agent_id': agent.id})
                
                current_app.logger.info(f"Agent {agent.name} disconnected")
                
        except Exception as e:
            current_app.logger.error(f"Disconnect error: {str(e)}")
    
    return socketio