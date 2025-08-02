from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import os
import tempfile
import time
from werkzeug.utils import secure_filename
from backend.db import db

api_routes_v2 = Blueprint('api_v2', __name__)

@api_routes_v2.route('/speech-to-task', methods=['GET', 'POST'])
def speech_to_task():
    """Simple speech to text endpoint using OpenAI API"""
    # Handle GET request for testing
    if request.method == 'GET':
        api_key = os.environ.get('OPENAI_API_KEY')
        return jsonify({
            'status': 'ready',
            'api_key_configured': bool(api_key),
            'api_key_prefix': api_key[:10] + '...' if api_key else None
        }), 200
    
    # POST requires login
    from flask_login import current_user
    if not current_user.is_authenticated:
        return jsonify({'error': 'Login required'}), 401
    
    # Log request
    current_app.logger.info("Speech-to-task POST request received")
    
    # Check for audio file
    if 'audio' not in request.files:
        current_app.logger.error("No audio file in request")
        return jsonify({'error': 'No audio file'}), 400
    
    # Check API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        current_app.logger.error("No API key configured")
        return jsonify({'error': 'OpenAI API key not configured'}), 400
    
    # Get audio file
    audio_file = request.files['audio']
    current_app.logger.info(f"Received audio file: {audio_file.filename}")
    
    # Check file size (Heroku timeout workaround)
    audio_file.seek(0, 2)  # Seek to end
    file_size = audio_file.tell()
    audio_file.seek(0)  # Reset to beginning
    
    if file_size > 1024 * 1024:  # 1MB limit for immediate processing
        current_app.logger.warning(f"Audio file too large: {file_size} bytes")
        return jsonify({
            'error': 'Audio file too large. Please record a shorter message (max 30 seconds).'
        }), 413
    
    # Create temp file
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            audio_file.save(tmp.name)
            temp_path = tmp.name
            current_app.logger.info(f"Saved audio to: {temp_path}, size: {file_size}")
    except Exception as e:
        current_app.logger.error(f"Failed to save audio: {e}")
        return jsonify({'error': 'Failed to save audio file'}), 500
    
    # Try to transcribe with retries and better error handling
    transcription_text = None
    last_error = None
    
    # Try up to 3 times with different configurations
    retry_configs = [
        {'timeout': 20.0, 'connect': 3.0},  # Faster timeout first
        {'timeout': 25.0, 'connect': 5.0},  # Standard timeout
        {'timeout': 15.0, 'connect': 2.0},  # Very fast timeout as last resort
    ]
    
    for attempt, config in enumerate(retry_configs):
        try:
            from openai import OpenAI
            import httpx
            import time
            
            current_app.logger.info(f"Transcription attempt {attempt + 1}/3 with timeout {config['timeout']}s")
            
            # Add small delay between retries
            if attempt > 0:
                time.sleep(1)
            
            # Create client with current timeout config
            http_client = httpx.Client(
                timeout=httpx.Timeout(config['timeout'], connect=config['connect']),
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            
            client = OpenAI(
                api_key=api_key,
                http_client=http_client,
                max_retries=0  # No internal retries
            )
            
            # Open file and transcribe
            with open(temp_path, 'rb') as f:
                current_app.logger.info(f"Calling Whisper API (attempt {attempt + 1})...")
                start_time = time.time()
                
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en",  # Force English for faster processing
                    response_format="text"  # Get text directly, simpler parsing
                )
                
                elapsed = time.time() - start_time
                current_app.logger.info(f"Transcription successful in {elapsed:.2f}s: {result[:50]}...")
                
                transcription_text = result
                
                # Close client immediately
                try:
                    http_client.close()
                except:
                    pass
                    
                break  # Success, exit retry loop
                
        except Exception as e:
            last_error = e
            error_msg = str(e)
            current_app.logger.error(f"Attempt {attempt + 1} failed: {type(e).__name__}: {error_msg}")
            
            # Close client on error
            try:
                if 'http_client' in locals():
                    http_client.close()
            except:
                pass
            
            # Don't retry on certain errors
            if 'Invalid API key' in error_msg or 'Incorrect API key' in error_msg:
                break
    
    # Clean up temp file
    try:
        os.unlink(temp_path)
    except:
        pass
    
    # Return result or error
    if transcription_text:
        return jsonify({'transcribed_text': transcription_text}), 200
    else:
        # Detailed error response
        error_msg = str(last_error) if last_error else "Unknown error"
        error_type = type(last_error).__name__ if last_error else "Unknown"
        
        current_app.logger.error(f"All transcription attempts failed. Last error: {error_type}: {error_msg}")
        
        if 'timeout' in error_msg.lower() or error_type == 'TimeoutError':
            return jsonify({
                'error': 'Request timed out. Please try recording a shorter message (under 30 seconds).'
            }), 504
        elif 'Invalid API key' in error_msg or 'Incorrect API key' in error_msg:
            return jsonify({
                'error': 'Invalid OpenAI API key. Please check your configuration.'
            }), 401
        elif 'connection' in error_msg.lower() or 'ConnectError' in error_type:
            return jsonify({
                'error': 'Failed to connect to OpenAI. This may be a temporary network issue. Please try again.'
            }), 503
        else:
            return jsonify({
                'error': f'Transcription failed after 3 attempts: {error_msg}'
            }), 500

@api_routes_v2.route('/test-api-key', methods=['GET'])
def test_api_key():
    """Test if OpenAI API key is configured"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        # Mask the key for security
        masked = api_key[:8] + '...' + api_key[-4:]
        return jsonify({'status': 'configured', 'key': masked}), 200
    else:
        return jsonify({'status': 'not configured'}), 200

@api_routes_v2.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'ok', 'message': 'Speech endpoint is alive'}), 200

@api_routes_v2.route('/speech-to-task-base64', methods=['POST'])
@login_required
def speech_to_task_base64():
    """Alternative speech endpoint using base64 encoding"""
    try:
        data = request.json
        if not data or 'audio' not in data:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Get base64 audio data
        import base64
        audio_base64 = data['audio']
        
        # Decode base64 to bytes
        try:
            # Remove data URL prefix if present
            if ',' in audio_base64:
                audio_base64 = audio_base64.split(',')[1]
            audio_bytes = base64.b64decode(audio_base64)
        except Exception as e:
            return jsonify({'error': f'Invalid base64 audio data: {str(e)}'}), 400
        
        # Check size
        if len(audio_bytes) > 1024 * 1024:  # 1MB limit
            return jsonify({'error': 'Audio file too large (max 1MB)'}), 413
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
            tmp.write(audio_bytes)
            temp_path = tmp.name
        
        # Use simpler OpenAI client
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            os.unlink(temp_path)
            return jsonify({'error': 'OpenAI API key not configured'}), 400
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            with open(temp_path, 'rb') as f:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="en"
                )
            
            os.unlink(temp_path)
            return jsonify({'transcribed_text': result.text}), 200
            
        except Exception as e:
            os.unlink(temp_path)
            return jsonify({'error': f'Transcription failed: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Request processing failed: {str(e)}'}), 500

@api_routes_v2.route('/test-openai-connection', methods=['GET'])
def test_openai_connection():
    """Test OpenAI connectivity directly"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return jsonify({'error': 'No API key configured'}), 400
    
    try:
        from openai import OpenAI
        import httpx
        
        # Test with same client configuration
        http_client = httpx.Client(
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True
        )
        
        client = OpenAI(
            api_key=api_key,
            http_client=http_client,
            max_retries=0
        )
        
        # Try a simple API call
        current_app.logger.info("Testing OpenAI connection...")
        models = client.models.list()
        
        http_client.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Successfully connected to OpenAI',
            'models_count': len(list(models))
        }), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"OpenAI connection test failed: {e}")
        current_app.logger.error(f"Full trace: {error_details}")
        
        return jsonify({
            'status': 'error',
            'error': str(e),
            'error_type': type(e).__name__,
            'details': error_details
        }), 500

@api_routes_v2.route('/schedule', methods=['POST'])
@login_required
def schedule_job():
    """Relay scheduling request to agent and save to database"""
    try:
        data = request.json
        from app import socketio
        from backend.models import ScheduledJob
        
        # Generate job group ID
        job_group_id = str(uuid.uuid4())
        
        # Prepare jobs for agent
        jobs = []
        
        # Extract scheduling parameters
        target_hwnd = data['target_hwnd']
        target_title = data.get('target_title', '')
        start_time = datetime.fromisoformat(data['start_time'])
        repetitions = data['repetitions']
        interval_seconds = data['interval_seconds']
        use_different_messages = data.get('use_different_messages', False)
        
        if use_different_messages:
            # Multiple different messages
            messages = data['messages']
            for i, message in enumerate(messages[:repetitions]):
                scheduled_time = start_time + timedelta(seconds=i * interval_seconds)
                
                # Save to database
                db_job = ScheduledJob(
                    user_id=current_user.id,
                    job_group_id=job_group_id,
                    message_text=message,
                    target_hwnd=target_hwnd,
                    target_title_snapshot=target_title,
                    scheduled_time=scheduled_time,
                    status='PENDING'
                )
                db.session.add(db_job)
                
                jobs.append({
                    'id': db_job.id,
                    'message_text': message,
                    'target_hwnd': target_hwnd,
                    'target_title': target_title,
                    'scheduled_time': scheduled_time.isoformat(),
                    'job_group_id': job_group_id
                })
        else:
            # Single message repeated
            message = data['message']
            for i in range(repetitions):
                scheduled_time = start_time + timedelta(seconds=i * interval_seconds)
                
                # Save to database
                db_job = ScheduledJob(
                    user_id=current_user.id,
                    job_group_id=job_group_id,
                    message_text=message,
                    target_hwnd=target_hwnd,
                    target_title_snapshot=target_title,
                    scheduled_time=scheduled_time,
                    status='PENDING'
                )
                db.session.add(db_job)
                
                jobs.append({
                    'id': db_job.id,
                    'message_text': message,
                    'target_hwnd': target_hwnd,
                    'target_title': target_title,
                    'scheduled_time': scheduled_time.isoformat(),
                    'job_group_id': job_group_id
                })
        
        # Commit to database first
        db.session.commit()
        
        # Then send to agent
        socketio.emit('schedule_job', {
            'job_group_id': job_group_id,
            'jobs': jobs
        })
        
        return jsonify({
            'job_group_id': job_group_id,
            'message': 'Schedule request sent to agent'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Schedule error: {str(e)}")
        return jsonify({'error': 'Failed to schedule job'}), 500

@api_routes_v2.route('/jobs', methods=['GET'])
@login_required
def get_jobs():
    """Request job list from agent and return cached data"""
    from app import socketio
    from backend.websocket_handlers_v2 import agent_jobs
    
    # Request fresh data from agent
    socketio.emit('get_jobs', {})
    
    # Return cached jobs immediately if available
    all_job_groups = []
    for agent_id, job_groups in agent_jobs.items():
        all_job_groups.extend(job_groups)
    
    return jsonify(all_job_groups), 200

@api_routes_v2.route('/jobs/<int:job_id>', methods=['PUT'])
@login_required
def update_job(job_id):
    """Relay job update to agent"""
    try:
        data = request.json
        from app import socketio
        
        update_data = {'job_id': job_id}
        
        if 'message_text' in data:
            update_data['message_text'] = data['message_text']
        
        if 'target_hwnd' in data:
            update_data['target_hwnd'] = data['target_hwnd']
            update_data['target_title'] = data.get('target_title', '')
        
        socketio.emit('update_job', update_data)
        
        return jsonify({'message': 'Update request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Update job error: {str(e)}")
        return jsonify({'error': 'Failed to update job'}), 500

@api_routes_v2.route('/jobs/<int:job_id>', methods=['DELETE'])
@login_required
def cancel_job(job_id):
    """Delete job from both agent and database"""
    try:
        from app import socketio
        from backend.models import ScheduledJob
        
        # Delete from database
        job = ScheduledJob.query.get(job_id)
        if job and job.user_id == current_user.id:
            db.session.delete(job)
            db.session.commit()
        
        # Notify agent to delete the job
        socketio.emit('delete_job_history', {'job_id': job_id})
        
        return jsonify({'message': 'Job deleted successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete job error: {str(e)}")
        return jsonify({'error': 'Failed to delete job'}), 500

@api_routes_v2.route('/jobs/<int:job_id>/delete-history', methods=['DELETE'])
@login_required
def delete_job_history(job_id):
    """Delete a sent job from history"""
    try:
        from app import socketio
        socketio.emit('delete_job_history', {'job_id': job_id})
        
        return jsonify({'message': 'Delete request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete job history error: {str(e)}")
        return jsonify({'error': 'Failed to delete job history'}), 500

@api_routes_v2.route('/jobs/<int:job_id>/reschedule', methods=['POST'])
@login_required
def reschedule_job(job_id):
    """Relay reschedule request to agent"""
    try:
        data = request.json
        from app import socketio
        
        socketio.emit('reschedule_job', {
            'job_id': job_id,
            'new_scheduled_time': data['new_scheduled_time']
        })
        
        return jsonify({'message': 'Reschedule request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Reschedule job error: {str(e)}")
        return jsonify({'error': 'Failed to reschedule job'}), 500

@api_routes_v2.route('/jobs/delete-all/<status>', methods=['DELETE'])
@login_required
def delete_all_by_status(status):
    """Delete all jobs with a specific status"""
    try:
        from app import socketio
        from backend.models import ScheduledJob
        
        # Validate status
        valid_statuses = ['PENDING', 'EXPIRED', 'SENT']
        if status.upper() not in valid_statuses:
            return jsonify({'error': 'Invalid status'}), 400
        
        # Delete from database
        if status.upper() == 'EXPIRED':
            # For expired, delete pending jobs with past scheduled time
            now = datetime.utcnow()
            ScheduledJob.query.filter(
                ScheduledJob.user_id == current_user.id,
                ScheduledJob.status == 'PENDING',
                ScheduledJob.scheduled_time < now
            ).delete()
            # Also delete any explicitly marked as expired
            ScheduledJob.query.filter(
                ScheduledJob.user_id == current_user.id,
                ScheduledJob.status == 'EXPIRED'
            ).delete()
        else:
            # Delete all jobs with the specified status
            ScheduledJob.query.filter(
                ScheduledJob.user_id == current_user.id,
                ScheduledJob.status == status.upper()
            ).delete()
        
        db.session.commit()
        
        # Notify agent to delete all jobs with this status
        socketio.emit('delete_all_by_status', {'status': status.upper()})
        
        return jsonify({'message': f'All {status} jobs deleted successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete all by status error: {str(e)}")
        return jsonify({'error': f'Failed to delete all {status} jobs'}), 500

@api_routes_v2.route('/jobs/purge-all', methods=['DELETE'])
@login_required
def purge_all_jobs():
    """Delete all jobs for the current user"""
    try:
        from app import socketio
        from backend.models import ScheduledJob
        
        # Delete all jobs from database
        ScheduledJob.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        # Notify agent to purge all jobs
        socketio.emit('purge_all_jobs', {})
        
        return jsonify({'message': 'All jobs purged successfully'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Purge all jobs error: {str(e)}")
        return jsonify({'error': 'Failed to purge all jobs'}), 500

@api_routes_v2.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Request saved transcripts from agent and return cached data"""
    from app import socketio
    from backend.websocket_handlers_v2 import agent_transcripts
    
    # Request fresh data from agent
    socketio.emit('get_transcripts', {})
    
    # Return cached transcripts immediately if available
    all_transcripts = []
    for agent_id, transcripts in agent_transcripts.items():
        all_transcripts.extend(transcripts)
    
    return jsonify(all_transcripts), 200

@api_routes_v2.route('/save-message', methods=['POST'])
@login_required
def save_message():
    """Save a message to the agent's transcript database"""
    try:
        data = request.json
        message_text = data.get('text', '').strip()
        
        if not message_text:
            return jsonify({'error': 'Message text is required'}), 400
        
        from app import socketio
        
        # Send save request to agent
        socketio.emit('save_transcript', {
            'text': message_text,
            'created_at': datetime.utcnow().isoformat()
        })
        
        return jsonify({'message': 'Save request sent to agent'}), 201
        
    except Exception as e:
        current_app.logger.error(f"Save message error: {str(e)}")
        return jsonify({'error': 'Failed to save message'}), 500

@api_routes_v2.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a saved message/transcript"""
    try:
        from app import socketio
        
        # Send delete request to agent
        socketio.emit('delete_transcript', {'id': task_id})
        
        return jsonify({'message': 'Delete request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete task error: {str(e)}")
        return jsonify({'error': 'Failed to delete task'}), 500

@api_routes_v2.route('/windows', methods=['GET'])
@login_required
def get_windows():
    """Get list of available windows from connected agents"""
    # In V2, windows are managed by the agent and sent via WebSocket
    # This endpoint exists for compatibility but returns empty list
    # The frontend should rely on WebSocket updates instead
    return jsonify([])

@api_routes_v2.route('/jobs/delete-all/<status>', methods=['DELETE'])
@login_required
def delete_all_by_status(status):
    """Delete all jobs by status (PENDING, EXPIRED, SENT)"""
    try:
        from app import socketio
        
        # Validate status
        valid_statuses = ['PENDING', 'EXPIRED', 'SENT']
        status = status.upper()
        if status not in valid_statuses:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        # Send delete request to agent
        socketio.emit('delete_all_by_status', {'status': status})
        
        return jsonify({'message': f'Delete all {status} jobs request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Delete all by status error: {str(e)}")
        return jsonify({'error': f'Failed to delete all {status} jobs'}), 500

@api_routes_v2.route('/jobs/purge-all', methods=['DELETE'])
@login_required
def purge_all_jobs():
    """Purge all jobs from the system"""
    try:
        from app import socketio
        
        # Send purge request to agent
        socketio.emit('purge_all_jobs', {})
        
        return jsonify({'message': 'Purge all jobs request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Purge all jobs error: {str(e)}")
        return jsonify({'error': 'Failed to purge all jobs'}), 500

@api_routes_v2.route('/agent/status', methods=['GET'])
@login_required
def get_agent_status():
    """Get current agent connection status"""
    try:
        from backend.websocket_handlers_v2 import connected_agents
        
        agents = []
        for sid, agent in connected_agents.items():
            agents.append({
                'id': agent.id,
                'name': agent.name,
                'connected': True,
                'last_seen': agent.last_seen.isoformat() if agent.last_seen else None
            })
        
        return jsonify({
            'agents': agents,
            'count': len(agents)
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get agent status error: {str(e)}")
        return jsonify({'error': 'Failed to get agent status'}), 500