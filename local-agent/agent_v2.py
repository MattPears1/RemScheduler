import os
import sys
import time
import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
import configparser
import socketio
import win32gui
import win32con
import win32api
import win32process
import win32clipboard
import psutil
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LocalAgent')

class LocalAgentV2:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.server_url = self.config.get('server', 'url', fallback='http://localhost:5000')
        self.username = self.config.get('auth', 'username', fallback='')
        self.password = self.config.get('auth', 'password', fallback='')
        
        if not self.username or not self.password:
            logger.error("No username/password found in config.ini")
            sys.exit(1)
        
        # Initialize database
        self.init_database()
        
        # Initialize scheduler
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Initialize SocketIO client
        self.sio = socketio.Client()
        self.setup_handlers()
        
        # Window discovery interval
        self.discovery_interval = 15
        self.last_discovery = 0
        self.connected = False
        self.windows = []
        
        # Load and reschedule existing jobs
        self.reschedule_pending_jobs()
        
        # Schedule cleanup of old sent messages
        self.scheduler.add_job(
            func=self.cleanup_old_messages,
            trigger="interval",
            hours=24,  # Run once per day
            id="cleanup_old_messages",
            replace_existing=True
        )
        self.cleanup_old_messages()  # Run once on startup
    
    def init_database(self):
        """Initialize local SQLite database"""
        self.db_path = 'local_messages.db'
        # Set up datetime adapter for SQLite
        sqlite3.register_adapter(datetime, lambda dt: dt.isoformat())
        sqlite3.register_converter("timestamp", lambda b: datetime.fromisoformat(b.decode()))
        
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute('PRAGMA journal_mode=WAL')
        cursor.execute('PRAGMA busy_timeout=5000')  # 5 second timeout
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_group_id TEXT NOT NULL,
                message_text TEXT NOT NULL,
                target_hwnd INTEGER NOT NULL,
                target_title TEXT,
                scheduled_time TIMESTAMP NOT NULL,
                status TEXT DEFAULT 'PENDING',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                executed_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized")
    
    def setup_handlers(self):
        """Set up SocketIO event handlers"""
        
        @self.sio.event
        def connect():
            logger.info(f"Connected to server at {self.server_url}")
            self.connected = True
            # Authenticate immediately
            self.sio.emit('agent_auth', {
                'username': self.username,
                'password': self.password
            })
        
        @self.sio.event
        def disconnect():
            logger.info("Disconnected from server")
            self.connected = False
        
        @self.sio.event
        def auth_success(data):
            logger.info(f"Authentication successful. Agent ID: {data['agent_id']}")
            # Send initial window list
            self.send_window_list()
            # Send current job status
            self.send_job_status()
        
        @self.sio.event
        def auth_error(data):
            logger.error(f"Authentication failed: {data['error']}")
            self.connected = False
        
        @self.sio.event
        def schedule_job(data):
            """Handle job scheduling from server"""
            logger.info(f"=== RECEIVED SCHEDULE REQUEST ===")
            logger.info(f"Job group ID: {data.get('job_group_id', 'N/A')}")
            logger.info(f"Number of jobs: {len(data.get('jobs', []))}")
            for i, job in enumerate(data.get('jobs', [])):
                logger.info(f"Job {i+1}: {job.get('message_text', '')[:50]}... at {job.get('scheduled_time', 'N/A')}")
            self.handle_schedule_request(data)
        
        @self.sio.event
        def get_jobs(data):
            """Handle request for job list"""
            self.send_job_status()
        
        @self.sio.event
        def update_job(data):
            """Handle job update request"""
            self.handle_job_update(data)
        
        @self.sio.event
        def cancel_job(data):
            """Handle job cancellation"""
            self.handle_job_cancel(data)
        
        @self.sio.event
        def delete_job_history(data):
            """Delete job from history"""
            self.delete_job_history(data['job_id'])
        
        @self.sio.event
        def save_transcript(data):
            """Save transcript locally"""
            self.save_transcript(data['text'])
        
        @self.sio.event
        def get_transcripts(data):
            """Send saved transcripts"""
            self.send_transcripts()
    
    def handle_schedule_request(self, data):
        """Handle scheduling request from server"""
        try:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            job_group_id = data['job_group_id']
            jobs = data['jobs']
            
            for job in jobs:
                # Insert job into database
                cursor.execute('''
                    INSERT INTO scheduled_jobs 
                    (job_group_id, message_text, target_hwnd, target_title, scheduled_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    job_group_id,
                    job['message_text'],
                    job['target_hwnd'],
                    job.get('target_title', ''),
                    job['scheduled_time']
                ))
                
                job_id = cursor.lastrowid
                
                # Schedule with APScheduler
                # Parse ISO format datetime and convert to timezone-aware datetime
                scheduled_str = job['scheduled_time'].replace('Z', '+00:00')
                run_time = datetime.fromisoformat(scheduled_str)
                
                # Ensure run_time is timezone-aware
                if run_time.tzinfo is None:
                    run_time = pytz.UTC.localize(run_time)
                
                # Convert UTC time to local time for scheduling
                # This ensures the job runs at the time the user selected in their local timezone
                local_tz = pytz.timezone('Europe/London')  # Adjust this to your timezone
                run_time_local = run_time.astimezone(local_tz)
                logger.info(f"Scheduling job {job_id}: UTC={run_time}, Local={run_time_local}")
                
                # Get current time as timezone-aware
                now_local = datetime.now(local_tz)
                
                if run_time_local > now_local:
                    self.scheduler.add_job(
                        func=self.execute_job,
                        trigger=DateTrigger(run_date=run_time_local),
                        args=[job_id],
                        id=f"job_{job_id}",
                        replace_existing=True
                    )
                    logger.info(f"Scheduled job {job_id} for {run_time_local} (local time)")
            
            conn.commit()
            conn.close()
            
            # Notify server of success
            self.sio.emit('schedule_success', {
                'job_group_id': job_group_id,
                'jobs_created': len(jobs)
            })
            
            # Send updated job list
            self.send_job_status()
            
        except Exception as e:
            logger.error(f"Failed to schedule jobs: {str(e)}")
            self.sio.emit('schedule_error', {
                'error': str(e)
            })
    
    def execute_job(self, job_id):
        """Execute a scheduled job"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        try:
            # Get job details
            cursor.execute('SELECT * FROM scheduled_jobs WHERE id = ?', (job_id,))
            job = cursor.fetchone()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Extract job data
            _, _, message_text, target_hwnd, target_title, _, status, *_ = job
            
            if status != 'PENDING':
                logger.info(f"Job {job_id} already processed, status: {status}")
                return
            
            logger.info(f"Executing job {job_id}: {message_text[:50]}...")
            
            # Check if window still exists
            if not win32gui.IsWindow(target_hwnd):
                raise Exception("Target window not found")
            
            # Bring window to foreground
            win32gui.SetForegroundWindow(target_hwnd)
            time.sleep(0.2)
            
            # Clear any existing text (Ctrl+A)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, 0, 0)
            win32api.keybd_event(ord('A'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
            
            # Copy to clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(message_text)
            win32clipboard.CloseClipboard()
            
            # Paste (Ctrl+V)
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, 0, 0)
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Wait for paste to complete
            time.sleep(5)
            
            # Send Enter
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            # Update job status
            cursor.execute('''
                UPDATE scheduled_jobs 
                SET status = 'SENT', executed_at = ?
                WHERE id = ?
            ''', (datetime.now(timezone.utc), job_id))
            
            logger.info(f"Successfully executed job {job_id}")
            
            # Notify server if connected
            if self.connected:
                self.sio.emit('job_complete', {'job_id': job_id})
            
        except Exception as e:
            logger.error(f"Failed to execute job {job_id}: {str(e)}")
            
            # Update job status
            cursor.execute('''
                UPDATE scheduled_jobs 
                SET status = 'FAILED', error_message = ?
                WHERE id = ?
            ''', (str(e), job_id))
            
            # Notify server if connected
            if self.connected:
                self.sio.emit('job_failed', {
                    'job_id': job_id,
                    'reason': str(e)
                })
        
        finally:
            conn.commit()
            conn.close()
            
            # Send updated status
            if self.connected:
                self.send_job_status()
    
    def get_command_windows(self):
        """Get all command prompt windows"""
        windows = []
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                
                try:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name().lower()
                    
                    if any(name in process_name for name in ['cmd.exe', 'powershell.exe', 'wt.exe', 'windowsterminal.exe']):
                        windows.append({
                            'hwnd': hwnd,
                            'title': window_text,
                            'process': process_name,
                            'pid': pid
                        })
                except Exception as e:
                    logger.debug(f"Error getting process info for hwnd {hwnd}: {str(e)}")
            
            return True
        
        win32gui.EnumWindows(enum_handler, None)
        return windows
    
    def send_window_list(self):
        """Send current window list to server"""
        self.windows = self.get_command_windows()
        logger.info(f"Found {len(self.windows)} command windows")
        
        if self.connected:
            self.sio.emit('agent_sends_window_list', {'windows': self.windows})
        
        self.last_discovery = time.time()
    
    def send_job_status(self):
        """Send current job status to server"""
        if not self.connected:
            return
        
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        # Get all jobs grouped by job_group_id
        cursor.execute('''
            SELECT job_group_id, id, message_text, target_hwnd, target_title, 
                   scheduled_time, status, error_message
            FROM scheduled_jobs
            ORDER BY scheduled_time
        ''')
        
        jobs_by_group = {}
        for row in cursor.fetchall():
            group_id = row[0]
            if group_id not in jobs_by_group:
                jobs_by_group[group_id] = {
                    'job_group_id': group_id,
                    'target_hwnd': row[3],
                    'target_title': row[4],
                    'jobs': []
                }
            
            jobs_by_group[group_id]['jobs'].append({
                'id': row[1],
                'message_text': row[2],
                'scheduled_time': row[5].isoformat() if isinstance(row[5], datetime) else row[5],
                'status': row[6],
                'error_message': row[7]
            })
        
        conn.close()
        
        self.sio.emit('agent_jobs_status', {
            'job_groups': list(jobs_by_group.values())
        })
    
    def handle_job_update(self, data):
        """Handle job update request"""
        try:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            job_id = data['job_id']
            
            # Update message if provided
            if 'message_text' in data:
                cursor.execute(
                    'UPDATE scheduled_jobs SET message_text = ? WHERE id = ?',
                    (data['message_text'], job_id)
                )
            
            # Update window if provided
            if 'target_hwnd' in data:
                cursor.execute(
                    'UPDATE scheduled_jobs SET target_hwnd = ?, target_title = ? WHERE id = ?',
                    (data['target_hwnd'], data.get('target_title', ''), job_id)
                )
            
            conn.commit()
            conn.close()
            
            self.sio.emit('update_success', {'job_id': job_id})
            self.send_job_status()
            
        except Exception as e:
            logger.error(f"Failed to update job: {str(e)}")
            self.sio.emit('update_error', {'error': str(e)})
    
    def handle_job_cancel(self, data):
        """Handle job cancellation"""
        try:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            job_id = data['job_id']
            
            # Cancel in scheduler
            try:
                self.scheduler.remove_job(f"job_{job_id}")
            except:
                pass  # Job might have already run
            
            # Update database
            cursor.execute(
                'UPDATE scheduled_jobs SET status = ? WHERE id = ?',
                ('CANCELLED', job_id)
            )
            
            conn.commit()
            conn.close()
            
            self.sio.emit('cancel_success', {'job_id': job_id})
            self.send_job_status()
            
        except Exception as e:
            logger.error(f"Failed to cancel job: {str(e)}")
            self.sio.emit('cancel_error', {'error': str(e)})
    
    def save_transcript(self, text):
        """Save transcript locally"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO transcripts (text) VALUES (?)', (text,))
        conn.commit()
        conn.close()
        logger.info("Transcript saved locally")
    
    def delete_job_history(self, job_id):
        """Delete job from history (only for SENT jobs)"""
        try:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Only delete if job is SENT
            cursor.execute('DELETE FROM scheduled_jobs WHERE id = ? AND status = "SENT"', (job_id,))
            
            if cursor.rowcount > 0:
                conn.commit()
                logger.info(f"Deleted job {job_id} from history")
                
                # Update job status
                self.send_job_status()
            else:
                logger.warning(f"Job {job_id} not found or not in SENT status")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to delete job history: {str(e)}")
    
    def send_transcripts(self):
        """Send saved transcripts to server"""
        if not self.connected:
            return
        
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        cursor.execute('SELECT id, text, created_at FROM transcripts ORDER BY created_at DESC')
        
        transcripts = []
        for row in cursor.fetchall():
            transcripts.append({
                'id': row[0],
                'text': row[1],
                'created_at': row[2].isoformat() if isinstance(row[2], datetime) else row[2]
            })
        
        conn.close()
        
        self.sio.emit('agent_transcripts', {'transcripts': transcripts})
    
    def reschedule_pending_jobs(self):
        """Reschedule pending jobs on startup"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, scheduled_time 
            FROM scheduled_jobs 
            WHERE status = 'PENDING' AND scheduled_time > ?
        ''', (datetime.now(timezone.utc).isoformat(),))
        
        for job_id, scheduled_time in cursor.fetchall():
            # Parse stored datetime string
            run_time = datetime.fromisoformat(scheduled_time)
            
            # Ensure it's timezone-aware
            if run_time.tzinfo is None:
                run_time = pytz.UTC.localize(run_time)
            
            # Convert UTC time to local time for scheduling
            local_tz = pytz.timezone('Europe/London')  # Adjust this to your timezone
            run_time_local = run_time.astimezone(local_tz)
            now_local = datetime.now(local_tz)
            
            # Only schedule if still in the future
            if run_time_local > now_local:
                self.scheduler.add_job(
                    func=self.execute_job,
                    trigger=DateTrigger(run_date=run_time_local),
                    args=[job_id],
                    id=f"job_{job_id}",
                    replace_existing=True
                )
                logger.info(f"Rescheduled job {job_id} for {run_time_local} (local time)")
        
        conn.close()
    
    def cleanup_old_messages(self):
        """Delete sent messages older than 7 days"""
        try:
            conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=5000')
            cursor = conn.cursor()
            
            # Calculate 7 days ago
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            # Delete old sent messages
            cursor.execute('''
                DELETE FROM scheduled_jobs 
                WHERE status = 'SENT' 
                AND executed_at < ?
            ''', (seven_days_ago.isoformat(),))
            
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                conn.commit()
                logger.info(f"Cleaned up {deleted_count} old sent messages")
                # Update job status
                self.send_job_status()
            else:
                logger.debug("No old messages to clean up")
                
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {str(e)}")
    
    def connect_with_retry(self):
        """Connect to server with exponential backoff retry"""
        retry_delay = 1
        max_delay = 60
        
        while True:
            try:
                logger.info(f"Attempting to connect to {self.server_url}")
                self.sio.connect(self.server_url)
                break
            except Exception as e:
                logger.error(f"Connection failed: {str(e)}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
    
    def run(self):
        """Main agent loop"""
        logger.info("Windows Local Agent V2 starting...")
        logger.info("Agent now stores all data locally and manages scheduling independently")
        
        # Connect to server
        self.connect_with_retry()
        
        try:
            while True:
                # Periodic window discovery
                if time.time() - self.last_discovery > self.discovery_interval:
                    self.send_window_list()
                
                # Sleep
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Agent shutting down...")
            self.scheduler.shutdown()
            self.sio.disconnect()

def main():
    agent = LocalAgentV2()
    agent.run()

if __name__ == '__main__':
    main()