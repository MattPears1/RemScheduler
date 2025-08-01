from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import openai
import os
import tempfile
from werkzeug.utils import secure_filename
from backend.db import db

api_routes_v2 = Blueprint('api_v2', __name__)

# Configure OpenAI client
openai_client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global openai_client
    if openai_client is None:
        api_key = os.environ.get('OPENAI_API_KEY')
        current_app.logger.info(f"Attempting to initialize OpenAI client. API key present: {bool(api_key)}")
        current_app.logger.info(f"API key length: {len(api_key) if api_key else 0}")
        
        if api_key:
            try:
                # Initialize with just the API key, no other parameters
                openai_client = openai.OpenAI(api_key=api_key)
                current_app.logger.info("OpenAI client initialized successfully")
            except Exception as e:
                current_app.logger.error(f"Failed to initialize OpenAI client: {type(e).__name__}: {str(e)}")
                import traceback
                current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            current_app.logger.error("No OPENAI_API_KEY found in environment variables")
            current_app.logger.error(f"Available env vars: {list(os.environ.keys())}")
    return openai_client

@api_routes_v2.route('/speech-to-task', methods=['POST'])
@login_required
def speech_to_task():
    """Convert speech audio to text"""
    try:
        current_app.logger.info("Speech-to-task endpoint called")
        
        client = get_openai_client()
        if not client:
            current_app.logger.error("OpenAI client not initialized")
            return jsonify({'error': 'OpenAI API key not configured'}), 500
            
        if 'audio' not in request.files:
            current_app.logger.error("No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        current_app.logger.info(f"Received audio file: {audio_file.filename}, content_type: {audio_file.content_type}")
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save temporary file with proper extension based on content type
        extension = '.webm'
        if audio_file.content_type:
            if 'wav' in audio_file.content_type:
                extension = '.wav'
            elif 'mp3' in audio_file.content_type:
                extension = '.mp3'
            elif 'mpeg' in audio_file.content_type:
                extension = '.mp3'
                
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
            current_app.logger.info(f"Saved audio to temp file: {temp_path}, size: {os.path.getsize(temp_path)} bytes")
        
        try:
            # Transcribe using OpenAI Whisper with new client API
            current_app.logger.info("Starting transcription with Whisper API")
            
            with open(temp_path, 'rb') as audio:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="en"  # Force English
                )
            
            # Get the transcribed text
            transcribed_text = transcript.text
            current_app.logger.info(f"Transcription successful: {transcribed_text[:50]}...")
            
            # Send to agent to save locally
            from app import socketio
            socketio.emit('save_transcript', {
                'text': transcribed_text
            })
            
            return jsonify({
                'transcribed_text': transcribed_text
            }), 201
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(f"Speech-to-task error: {str(e)}\nTraceback: {error_trace}")
        return jsonify({'error': f'Failed to process audio: {str(e)}'}), 500

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