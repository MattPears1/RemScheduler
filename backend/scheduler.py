import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from flask_socketio import SocketIO
from backend.db import db
from backend.models import ScheduledJob, SystemStatus

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Schedule the job checker to run every 30 seconds
        self.scheduler.add_job(
            func=self.check_and_execute_jobs,
            trigger="interval",
            seconds=30,
            id='job_checker',
            replace_existing=True
        )
        
        logger.info("Job scheduler initialized")
    
    def check_and_execute_jobs(self):
        """Check for due jobs and send them to agents"""
        with self.app.app_context():
            try:
                # Get system status
                system_status = SystemStatus.get_current_status()
                
                # Don't execute jobs if system is rate limited
                if system_status.rate_limited and system_status.reset_time:
                    if datetime.utcnow() < system_status.reset_time:
                        return
                    else:
                        # Reset time has passed, clear rate limit
                        system_status.rate_limited = False
                        system_status.reset_time = None
                        db.session.commit()
                
                # Find all pending jobs that are due
                due_jobs = ScheduledJob.query.filter(
                    ScheduledJob.status == 'PENDING',
                    ScheduledJob.scheduled_time <= datetime.utcnow()
                ).all()
                
                if due_jobs:
                    logger.info(f"Found {len(due_jobs)} due jobs")
                
                for job in due_jobs:
                    self.execute_job(job)
                
            except Exception as e:
                logger.error(f"Error in job checker: {str(e)}")
    
    def execute_job(self, job):
        """Send a job to the appropriate agent"""
        try:
            # Import here to avoid circular dependency
            from backend.websocket_handlers import agent_windows
            
            # Find an online agent with the target window
            target_agent = None
            for agent_id, windows in agent_windows.items():
                for window in windows:
                    if window['hwnd'] == job.target_hwnd:
                        target_agent = agent_id
                        break
                if target_agent:
                    break
            
            if not target_agent:
                # Window not found, mark job as failed
                job.status = 'FAILED'
                job.error_message = 'Target window not found'
                db.session.commit()
                
                # Notify clients
                self.socketio.emit('job_status_updated', {
                    'job_id': job.id,
                    'status': 'FAILED',
                    'error': 'Target window not found'
                })
                
                logger.warning(f"Job {job.id} failed: Target window not found")
                return
            
            # Send job to agent - broadcast to all connected agents for now
            self.socketio.emit('execute_job', {
                'job_id': job.id,
                'target_hwnd': job.target_hwnd,
                'message_text': job.message_text
            })
            
            logger.info(f"Sent job {job.id} to agent {target_agent}")
            
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {str(e)}")
            job.status = 'FAILED'
            job.error_message = str(e)
            db.session.commit()

# Global scheduler instance
scheduler = None

def init_scheduler(app, socketio):
    """Initialize the global scheduler"""
    global scheduler
    scheduler = JobScheduler(app, socketio)
    return scheduler