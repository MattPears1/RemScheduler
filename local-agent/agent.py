import os
import sys
import time
import json
import logging
import configparser
from datetime import datetime
import socketio
import win32gui
import win32con
import win32api
import win32process
import psutil

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

class WindowsLocalAgent:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)
        
        self.server_url = self.config.get('server', 'url', fallback='http://localhost:5000')
        self.username = self.config.get('auth', 'username', fallback='')
        self.password = self.config.get('auth', 'password', fallback='')
        
        if not self.username or not self.password:
            logger.error("No username/password found in config.ini")
            sys.exit(1)
        
        # Initialize SocketIO client
        self.sio = socketio.Client()
        self.setup_handlers()
        
        # Window discovery interval
        self.discovery_interval = 15  # seconds
        self.last_discovery = 0
        self.connected = False
        
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
        
        @self.sio.event
        def auth_error(data):
            logger.error(f"Authentication failed: {data['error']}")
            self.connected = False
        
        @self.sio.event
        def execute_job(data):
            logger.info(f"Received job: {data['job_id']}")
            self.execute_command(data)
    
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
    
    def get_command_windows(self):
        """Get all command prompt windows"""
        windows = []
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                
                try:
                    # Get process info
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    process = psutil.Process(pid)
                    process_name = process.name().lower()
                    
                    # Check if it's a command prompt or terminal
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
        windows = self.get_command_windows()
        logger.info(f"Found {len(windows)} command windows")
        
        self.sio.emit('agent_sends_window_list', {'windows': windows})
        self.last_discovery = time.time()
    
    def execute_command(self, job_data):
        """Execute a command in the specified window"""
        job_id = job_data['job_id']
        target_hwnd = job_data['target_hwnd']
        message_text = job_data['message_text']
        
        try:
            # Check if window still exists
            if not win32gui.IsWindow(target_hwnd):
                logger.error(f"Window {target_hwnd} no longer exists")
                self.sio.emit('job_failed', {
                    'job_id': job_id,
                    'reason': 'Target window not found'
                })
                return
            
            # Bring window to foreground
            win32gui.SetForegroundWindow(target_hwnd)
            time.sleep(0.1)  # Small delay to ensure window is active
            
            # Type the message
            for char in message_text:
                if char == '\n':
                    # Send Enter key for newlines
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                else:
                    # Type character
                    win32api.keybd_event(ord(char.upper()), 0, 0, 0)
                    win32api.keybd_event(ord(char.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.01)  # Small delay between keystrokes
            
            # Send final Enter to execute command
            time.sleep(0.1)
            win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
            win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            logger.info(f"Successfully executed job {job_id}")
            self.sio.emit('job_complete', {'job_id': job_id})
            
        except Exception as e:
            logger.error(f"Failed to execute job {job_id}: {str(e)}")
            self.sio.emit('job_failed', {
                'job_id': job_id,
                'reason': str(e)
            })
    
    def check_rate_limits(self):
        """Check all windows for rate limit messages"""
        windows = self.get_command_windows()
        
        for window in windows:
            try:
                # This is a placeholder - actual implementation would need to
                # read window text content, possibly using UI automation
                # For now, we'll skip this as it requires more complex implementation
                pass
            except Exception as e:
                logger.debug(f"Error checking window {window['hwnd']}: {str(e)}")
    
    def run(self):
        """Main agent loop"""
        logger.info("Windows Local Agent starting...")
        
        # Connect to server
        self.connect_with_retry()
        
        try:
            while True:
                # Periodic window discovery
                if self.connected and time.time() - self.last_discovery > self.discovery_interval:
                    self.send_window_list()
                
                # Check for rate limits
                if self.connected:
                    self.check_rate_limits()
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Agent shutting down...")
            self.sio.disconnect()

def main():
    agent = WindowsLocalAgent()
    agent.run()

if __name__ == '__main__':
    main()