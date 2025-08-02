from flask_socketio import emit, disconnect
from flask import request, current_app
from datetime import datetime
from backend.db import db
from backend.models import LocalAgent, ScheduledJob, User

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
            
            # Load existing jobs from database
            load_jobs_from_database(agent)
            
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
        """Receive job status from agent and persist to database"""
        try:
            if request.sid not in connected_agents:
                return
            
            agent = connected_agents[request.sid]
            job_groups = data.get('job_groups', [])
            
            # Store jobs for this agent
            agent_jobs[agent.id] = job_groups
            
            # Sync jobs to database
            sync_jobs_to_database(agent.user_id, job_groups)
            
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
    
    @socketio.on('agent_heartbeat')
    def handle_agent_heartbeat(data):
        """Handle heartbeat from agent"""
        if request.sid in connected_agents:
            agent = connected_agents[request.sid]
            agent.last_seen = datetime.utcnow()
            db.session.commit()
            current_app.logger.debug(f"Heartbeat from agent {agent.name}")
    
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
        current_app.logger.info(f"Connected agents: {len(connected_agents)}")
        current_app.logger.info(f"Agent windows: {list(agent_windows.keys())}")
        current_app.logger.info(f"Agent jobs: {list(agent_jobs.keys())}")
        
        # Send agent connection status
        if connected_agents:
            for sid, agent in connected_agents.items():
                current_app.logger.info(f"Emitting agent_connected for agent {agent.id}")
                emit('agent_connected', {
                    'agent_id': agent.id,
                    'agent_name': agent.name
                })
        else:
            current_app.logger.info("No connected agents to report")
        
        # Send current state to web client
        for agent_id, windows in agent_windows.items():
            current_app.logger.info(f"Emitting windows for agent {agent_id}: {len(windows)} windows")
            emit('windows_updated', {
                'agent_id': agent_id,
                'windows': windows
            })
        
        for agent_id, job_groups in agent_jobs.items():
            current_app.logger.info(f"Emitting jobs for agent {agent_id}: {len(job_groups)} groups")
            # Log details of first job group for debugging
            if job_groups and len(job_groups) > 0:
                first_group = job_groups[0]
                current_app.logger.info(f"First job group: {first_group.get('job_group_id')} with {len(first_group.get('jobs', []))} jobs")
            emit('jobs_updated', {
                'agent_id': agent_id,
                'job_groups': job_groups
            })
        
        for agent_id, transcripts in agent_transcripts.items():
            current_app.logger.info(f"Emitting transcripts for agent {agent_id}: {len(transcripts)} items")
            emit('transcripts_updated', {
                'agent_id': agent_id,
                'transcripts': transcripts
            })
    
    @socketio.on('get_jobs')
    def handle_web_get_jobs(data=None):
        """Forward job request to all connected agents"""
        current_app.logger.info("Web client requested jobs update")
        # Forward to all connected agents
        for sid in connected_agents:
            socketio.emit('get_jobs', {}, room=sid)
    
    @socketio.on('get_transcripts')
    def handle_web_get_transcripts(data=None):
        """Forward transcript request to all connected agents"""
        current_app.logger.info("Web client requested transcripts update")
        # Forward to all connected agents
        for sid in connected_agents:
            socketio.emit('get_transcripts', {}, room=sid)
    
    # Helper function to load jobs from database
    def load_jobs_from_database(agent):
        """Load pending jobs from database and send to agent"""
        try:
            # Get all pending jobs for this user
            pending_jobs = ScheduledJob.query.filter_by(
                user_id=agent.user_id,
                status='PENDING'
            ).order_by(ScheduledJob.scheduled_time).all()
            
            if pending_jobs:
                # Group jobs by job_group_id
                job_groups = {}
                for job in pending_jobs:
                    if job.job_group_id not in job_groups:
                        job_groups[job.job_group_id] = []
                    
                    job_groups[job.job_group_id].append({
                        'id': job.id,
                        'message_text': job.message_text,
                        'target_hwnd': job.target_hwnd,
                        'target_title': job.target_title_snapshot,
                        'scheduled_time': job.scheduled_time.isoformat(),
                        'job_group_id': job.job_group_id
                    })
                
                # Send each job group to agent
                for group_id, jobs in job_groups.items():
                    socketio.emit('schedule_job', {
                        'job_group_id': group_id,
                        'jobs': jobs
                    }, room=request.sid)
                    current_app.logger.info(f"Sent {len(jobs)} pending jobs (group {group_id}) to agent")
        
        except Exception as e:
            current_app.logger.error(f"Error loading jobs from database: {str(e)}")
    
    # Helper function to sync jobs to database
    def sync_jobs_to_database(user_id, job_groups):
        """Sync job groups from agent to backend database"""
        try:
            # Get all job IDs from agent
            agent_job_ids = set()
            for group in job_groups:
                for job in group.get('jobs', []):
                    # Use combination of group_id and message as unique identifier
                    agent_job_ids.add((job.get('job_group_id'), job.get('id')))
            
            # Mark missing jobs as deleted/cancelled if they were pending
            existing_jobs = ScheduledJob.query.filter_by(user_id=user_id).all()
            for job in existing_jobs:
                if (job.job_group_id, job.id) not in agent_job_ids and job.status == 'PENDING':
                    job.status = 'CANCELLED'
                    current_app.logger.info(f"Marked job {job.id} as CANCELLED (not in agent)")
            
            # Update or create jobs from agent
            for group in job_groups:
                for job in group.get('jobs', []):
                    # Find existing job or create new one
                    existing_job = ScheduledJob.query.filter_by(
                        user_id=user_id,
                        job_group_id=job.get('job_group_id'),
                        id=job.get('id')
                    ).first()
                    
                    if existing_job:
                        # Update existing job
                        existing_job.status = job.get('status', 'PENDING')
                        existing_job.error_message = job.get('error_message')
                        if job.get('executed_at'):
                            existing_job.executed_at = datetime.fromisoformat(job['executed_at'].replace('Z', '+00:00'))
                    else:
                        # Create new job
                        new_job = ScheduledJob(
                            user_id=user_id,
                            job_group_id=job.get('job_group_id'),
                            message_text=job.get('message_text', ''),
                            target_hwnd=job.get('target_hwnd', 0),
                            target_title_snapshot=job.get('target_title'),
                            scheduled_time=datetime.fromisoformat(job['scheduled_time'].replace('Z', '+00:00')),
                            status=job.get('status', 'PENDING'),
                            error_message=job.get('error_message'),
                            created_at=datetime.fromisoformat(job['created_at'].replace('Z', '+00:00')) if job.get('created_at') else datetime.utcnow()
                        )
                        if job.get('executed_at'):
                            new_job.executed_at = datetime.fromisoformat(job['executed_at'].replace('Z', '+00:00'))
                        db.session.add(new_job)
            
            db.session.commit()
            current_app.logger.info(f"Synced {len(job_groups)} job groups to database")
            
        except Exception as e:
            current_app.logger.error(f"Error syncing jobs to database: {str(e)}")
            db.session.rollback()
    
    return socketio