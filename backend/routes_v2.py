from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import os
import tempfile
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
    
    # Try to transcribe with short timeout
    try:
        from openai import OpenAI
        import httpx
        
        # Create client with shorter timeout for Heroku
        http_client = httpx.Client(
            timeout=httpx.Timeout(25.0, connect=5.0),  # Total 25s (under Heroku's 30s)
            follow_redirects=True
        )
        
        client = OpenAI(
            api_key=api_key,
            http_client=http_client,
            max_retries=0  # No retries to avoid timeout
        )
        current_app.logger.info("OpenAI client created with 25s timeout")
        
        # Open file and transcribe
        with open(temp_path, 'rb') as f:
            current_app.logger.info("Calling Whisper API...")
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en"  # Force English for faster processing
            )
        
        current_app.logger.info(f"Transcription successful: {result.text[:50]}...")
        
        # Clean up
        try:
            os.unlink(temp_path)
            http_client.close()
        except:
            pass
        
        return jsonify({'transcribed_text': result.text}), 200
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"Transcription failed: {e}")
        current_app.logger.error(f"Full error trace: {error_details}")
        
        # Clean up
        try:
            os.unlink(temp_path)
            if 'http_client' in locals():
                http_client.close()
        except:
            pass
        
        # Return error with actual details
        error_msg = str(e)
        error_type = type(e).__name__
        
        if 'timeout' in error_msg.lower() or error_type == 'TimeoutError':
            return jsonify({
                'error': 'Request timed out after 25 seconds. The audio may be too long to process.'
            }), 504
        elif 'connection' in error_msg.lower() or 'ConnectError' in error_type:
            # Connection errors on Heroku are often DNS/network related, not timeout
            return jsonify({
                'error': f'Connection failed to OpenAI servers. Error: {error_msg}. This appears to be a Heroku networking issue.'
            }), 503
        else:
            return jsonify({'error': f'Transcription failed: {error_type}: {error_msg}'}), 500

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
    """Relay job cancellation to agent"""
    try:
        from app import socketio
        socketio.emit('cancel_job', {'job_id': job_id})
        
        return jsonify({'message': 'Cancel request sent to agent'}), 200
        
    except Exception as e:
        current_app.logger.error(f"Cancel job error: {str(e)}")
        return jsonify({'error': 'Failed to cancel job'}), 500

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