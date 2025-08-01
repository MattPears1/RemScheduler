from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import uuid
import openai
import os
from werkzeug.utils import secure_filename
from backend.db import db
from backend.models import Task, ScheduledJob, PresetProfile, SystemStatus

api_routes = Blueprint('api', __name__)

# Configure OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')

@api_routes.route('/speech-to-task', methods=['POST'])
@login_required
def speech_to_task():
    """Convert speech audio to text and create a task"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Save temporary file
        temp_path = f"/tmp/{secure_filename(audio_file.filename)}"
        audio_file.save(temp_path)
        
        # Transcribe using OpenAI Whisper
        with open(temp_path, 'rb') as audio:
            transcript = openai.Audio.transcribe("whisper-1", audio)
        
        # Clean up temp file
        os.remove(temp_path)
        
        # Create task
        task = Task(
            user_id=current_user.id,
            transcribed_text=transcript['text']
        )
        db.session.add(task)
        db.session.commit()
        
        return jsonify({
            'task_id': task.id,
            'transcribed_text': task.transcribed_text
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Speech-to-task error: {str(e)}")
        return jsonify({'error': 'Failed to process audio'}), 500

@api_routes.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get all tasks for the current user"""
    tasks = Task.query.filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
    return jsonify([{
        'id': task.id,
        'text': task.transcribed_text,
        'created_at': task.created_at.isoformat()
    } for task in tasks])

@api_routes.route('/schedule', methods=['POST'])
@login_required
def schedule_job():
    """Schedule a job or sequence of jobs"""
    try:
        data = request.json
        
        # Check if system is rate limited
        system_status = SystemStatus.get_current_status()
        
        # Generate job group ID
        job_group_id = str(uuid.uuid4())
        
        # Extract scheduling parameters
        target_hwnd = data['target_hwnd']
        target_title = data.get('target_title', '')
        start_time = datetime.fromisoformat(data['start_time'])
        repetitions = data['repetitions']
        interval_seconds = data['interval_seconds']
        use_different_messages = data.get('use_different_messages', False)
        
        # Apply rate limit delay if active
        if system_status.rate_limited and system_status.reset_time:
            if start_time < system_status.reset_time:
                delay = system_status.reset_time - start_time
                start_time = system_status.reset_time
        
        jobs_created = []
        
        if use_different_messages:
            # Multiple different messages
            messages = data['messages']
            for i, message in enumerate(messages[:repetitions]):
                scheduled_time = start_time + timedelta(seconds=i * interval_seconds)
                
                job = ScheduledJob(
                    user_id=current_user.id,
                    job_group_id=job_group_id,
                    message_text=message,
                    target_hwnd=target_hwnd,
                    target_title_snapshot=target_title,
                    scheduled_time=scheduled_time
                )
                db.session.add(job)
                jobs_created.append(job)
        else:
            # Single message repeated
            message = data['message']
            for i in range(repetitions):
                scheduled_time = start_time + timedelta(seconds=i * interval_seconds)
                
                job = ScheduledJob(
                    user_id=current_user.id,
                    job_group_id=job_group_id,
                    message_text=message,
                    target_hwnd=target_hwnd,
                    target_title_snapshot=target_title,
                    scheduled_time=scheduled_time
                )
                db.session.add(job)
                jobs_created.append(job)
        
        db.session.commit()
        
        return jsonify({
            'job_group_id': job_group_id,
            'jobs_created': len(jobs_created),
            'first_scheduled_time': jobs_created[0].scheduled_time.isoformat() if jobs_created else None
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Schedule error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to schedule job'}), 500

@api_routes.route('/jobs/<int:job_id>', methods=['PUT'])
@login_required
def update_job(job_id):
    """Edit a scheduled job's message"""
    try:
        job = ScheduledJob.query.filter_by(id=job_id, user_id=current_user.id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'PENDING':
            return jsonify({'error': 'Can only edit pending jobs'}), 400
        
        data = request.json
        job.message_text = data['message_text']
        db.session.commit()
        
        return jsonify({'message': 'Job updated successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Update job error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update job'}), 500

@api_routes.route('/jobs/<int:job_id>', methods=['DELETE'])
@login_required
def cancel_job(job_id):
    """Cancel a scheduled job"""
    try:
        job = ScheduledJob.query.filter_by(id=job_id, user_id=current_user.id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'PENDING':
            return jsonify({'error': 'Can only cancel pending jobs'}), 400
        
        job.status = 'CANCELLED'
        db.session.commit()
        
        return jsonify({'message': 'Job cancelled successfully'})
        
    except Exception as e:
        current_app.logger.error(f"Cancel job error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to cancel job'}), 500

@api_routes.route('/jobs/<int:job_id>/reschedule', methods=['POST'])
@login_required
def reschedule_job(job_id):
    """Reschedule a job and maintain sequence timing"""
    try:
        job = ScheduledJob.query.filter_by(id=job_id, user_id=current_user.id).first()
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job.status != 'PENDING':
            return jsonify({'error': 'Can only reschedule pending jobs'}), 400
        
        data = request.json
        new_time = datetime.fromisoformat(data['new_scheduled_time'])
        
        # Calculate time delta
        time_delta = new_time - job.scheduled_time
        
        # Update the target job
        original_time = job.scheduled_time
        job.scheduled_time = new_time
        
        # Update all subsequent jobs in the same group
        subsequent_jobs = ScheduledJob.query.filter(
            ScheduledJob.job_group_id == job.job_group_id,
            ScheduledJob.status == 'PENDING',
            ScheduledJob.scheduled_time > original_time,
            ScheduledJob.id != job_id
        ).all()
        
        for subsequent_job in subsequent_jobs:
            subsequent_job.scheduled_time += time_delta
        
        db.session.commit()
        
        return jsonify({
            'message': 'Job rescheduled successfully',
            'jobs_affected': len(subsequent_jobs) + 1
        })
        
    except Exception as e:
        current_app.logger.error(f"Reschedule job error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to reschedule job'}), 500

@api_routes.route('/jobs', methods=['GET'])
@login_required
def get_jobs():
    """Get all scheduled jobs grouped by job_group_id"""
    try:
        # Get all jobs for current user
        jobs = ScheduledJob.query.filter_by(user_id=current_user.id).order_by(ScheduledJob.scheduled_time).all()
        
        # Group by job_group_id
        job_groups = {}
        for job in jobs:
            if job.job_group_id not in job_groups:
                job_groups[job.job_group_id] = {
                    'job_group_id': job.job_group_id,
                    'target_hwnd': job.target_hwnd,
                    'target_title': job.target_title_snapshot,
                    'jobs': []
                }
            
            job_groups[job.job_group_id]['jobs'].append({
                'id': job.id,
                'message_text': job.message_text,
                'scheduled_time': job.scheduled_time.isoformat(),
                'status': job.status,
                'error_message': job.error_message
            })
        
        return jsonify(list(job_groups.values()))
        
    except Exception as e:
        current_app.logger.error(f"Get jobs error: {str(e)}")
        return jsonify({'error': 'Failed to get jobs'}), 500

@api_routes.route('/preset-profiles', methods=['GET', 'POST'])
@login_required
def preset_profiles():
    """Get or create preset scheduling profiles"""
    if request.method == 'GET':
        profiles = PresetProfile.query.filter_by(user_id=current_user.id).all()
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'icon': p.icon,
            'start_delay_seconds': p.start_delay_seconds,
            'repetitions': p.repetitions,
            'interval_seconds': p.interval_seconds
        } for p in profiles])
    
    else:  # POST
        try:
            data = request.json
            profile = PresetProfile(
                user_id=current_user.id,
                name=data['name'],
                icon=data.get('icon', '⚡'),
                start_delay_seconds=data['start_delay_seconds'],
                repetitions=data['repetitions'],
                interval_seconds=data['interval_seconds']
            )
            db.session.add(profile)
            db.session.commit()
            
            return jsonify({
                'id': profile.id,
                'message': 'Profile created successfully'
            }), 201
            
        except Exception as e:
            current_app.logger.error(f"Create profile error: {str(e)}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create profile'}), 500

@api_routes.route('/windows', methods=['GET'])
@login_required
def get_windows():
    """Get list of available windows from connected agents"""
    # This will be populated by WebSocket connections from agents
    # For now, return empty list
    return jsonify([])