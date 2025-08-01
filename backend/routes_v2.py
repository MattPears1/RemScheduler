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
    try:
        # Handle GET request for testing
        if request.method == 'GET':
            api_key = os.environ.get('OPENAI_API_KEY')
            return jsonify({
                'status': 'ready',
                'api_key_configured': bool(api_key),
                'api_key_prefix': api_key[:10] + '...' if api_key else None
            }), 200
        
        # POST requires login
        from flask_login import login_required, current_user
        if not current_user.is_authenticated:
            return jsonify({'error': 'Login required'}), 401
        
        # Check for audio file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400
        
        # Check API key
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'OpenAI API key not set in Heroku config'}), 400
        
        # Save audio to temp file
        audio_file = request.files['audio']
        temp_fd, temp_path = tempfile.mkstemp(suffix='.webm')
        
        try:
            # Save the file
            with os.fdopen(temp_fd, 'wb') as f:
                audio_file.save(f)
            
            # Import OpenAI
            try:
                from openai import OpenAI
            except ImportError:
                return jsonify({'error': 'OpenAI library not installed'}), 500
            
            # Create client
            try:
                client = OpenAI(api_key=api_key)
            except Exception as e:
                return jsonify({'error': f'Failed to create OpenAI client: {str(e)}'}), 500
            
            # Call transcription API
            try:
                with open(temp_path, 'rb') as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )
                
                # Return text
                return jsonify({'transcribed_text': transcription.text}), 200
                
            except Exception as e:
                # API call failed
                error_msg = str(e)
                if 'connection' in error_msg.lower():
                    return jsonify({'error': 'Cannot connect to OpenAI API from Heroku'}), 503
                elif 'api_key' in error_msg.lower():
                    return jsonify({'error': 'Invalid OpenAI API key'}), 401
                else:
                    return jsonify({'error': f'OpenAI API error: {error_msg}'}), 500
                
        finally:
            # Clean up
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
    except Exception as e:
        # Catch any other errors to prevent 503
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Speech-to-task error: {str(e)}")
        current_app.logger.error(f"Traceback: {error_trace}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'type': type(e).__name__
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

@api_routes_v2.route('/schedule', methods=['POST'])
@login_required
def schedule_job():
    """Relay scheduling request to agent"""
    try:
        data = request.json
        from app import socketio
        
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
                jobs.append({
                    'message_text': message,
                    'target_hwnd': target_hwnd,
                    'target_title': target_title,
                    'scheduled_time': scheduled_time.isoformat()
                })
        else:
            # Single message repeated
            message = data['message']
            for i in range(repetitions):
                scheduled_time = start_time + timedelta(seconds=i * interval_seconds)
                jobs.append({
                    'message_text': message,
                    'target_hwnd': target_hwnd,
                    'target_title': target_title,
                    'scheduled_time': scheduled_time.isoformat()
                })
        
        # Send to agent
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


@api_routes_v2.route('/windows', methods=['GET'])
@login_required
def get_windows():
    """Get list of available windows from connected agents"""
    # In V2, windows are managed by the agent and sent via WebSocket
    # This endpoint exists for compatibility but returns empty list
    # The frontend should rely on WebSocket updates instead
    return jsonify([])

