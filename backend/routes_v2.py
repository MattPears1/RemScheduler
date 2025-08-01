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
try:
    if os.environ.get('OPENAI_API_KEY'):
        openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
except Exception as e:
    print(f"Failed to initialize OpenAI client: {e}")
    openai_client = None

@api_routes_v2.route('/speech-to-task', methods=['POST'])
@login_required
def speech_to_task():
    """Convert speech audio to text"""
    try:
        if not openai_client:
            return jsonify({'error': 'OpenAI API key not configured'}), 500
            
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save temporary file with proper extension
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # Transcribe using OpenAI Whisper with new client API
            with open(temp_path, 'rb') as audio:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language="en",  # Force English
                    prompt="Transcribe the following audio to English text."
                )
            
            # Get the transcribed text
            transcribed_text = transcript.text
            
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
        current_app.logger.error(f"Speech-to-task error: {str(e)}")
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
    """Request job list from agent"""
    from app import socketio
    socketio.emit('get_jobs', {})
    # Agent will respond via WebSocket with agent_jobs_status
    return jsonify({'message': 'Requesting jobs from agent'}), 200

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
    """Request saved transcripts from agent"""
    from app import socketio
    socketio.emit('get_transcripts', {})
    # Agent will respond via WebSocket with agent_transcripts
    return jsonify({'message': 'Requesting transcripts from agent'}), 200

@api_routes_v2.route('/windows', methods=['GET'])
@login_required
def get_windows():
    """Get list of available windows from connected agents"""
    # In V2, windows are managed by the agent and sent via WebSocket
    # This endpoint exists for compatibility but returns empty list
    # The frontend should rely on WebSocket updates instead
    return jsonify([])