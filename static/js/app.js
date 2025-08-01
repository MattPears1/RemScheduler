// Global state
const state = {
    user: null,
    socket: null,
    currentScreen: 'login',
    windows: [],
    currentTask: null,
    selectedJobGroup: null,
    mediaRecorder: null,
    audioChunks: []
};

// Socket.IO connection
function connectSocket() {
    console.log('🔌 Initializing Socket.IO connection...');
    state.socket = io();
    
    state.socket.on('connect', () => {
        console.log('✅ Connected to server');
        console.log('📡 Socket ID:', state.socket.id);
        // Notify server we're a web client
        console.log('🖥️ Notifying server we are a web client...');
        state.socket.emit('web_connect');
    });
    
    state.socket.on('windows_updated', (data) => {
        console.log('🪟 Windows updated:', data.windows);
        state.windows = data.windows;
        updateWindowsList();
    });
    
    state.socket.on('rate_limit_active', (data) => {
        console.log('⚠️ Rate limit active until:', data.reset_time);
        showRateLimitBanner(data.reset_time);
    });
    
    state.socket.on('job_status_updated', (data) => {
        console.log('📋 Job status updated:', data);
        
        // Show notification for sent messages
        if (data.status === 'SENT') {
            showMessageNotification('Message sent successfully!');
        }
        
        if (state.currentScreen === 'mission-control') {
            loadMissionControl();
        }
    });
    
    // Handle job updates from agent
    state.socket.on('jobs_updated', (data) => {
        console.log('📊 Jobs updated from agent:', data);
        if (state.currentScreen === 'mission-control') {
            displayJobGroups(data.job_groups);
        }
    });
    
    // Handle transcript updates from agent
    state.socket.on('transcripts_updated', (data) => {
        console.log('📝 Transcripts updated from agent:', data);
        if (state.currentScreen === 'saved-messages') {
            displaySavedMessages(data.transcripts);
        }
    });
    
    // Handle schedule confirmations
    state.socket.on('schedule_confirmed', (data) => {
        console.log('✅ Schedule confirmed:', data);
        showMessageNotification(`Successfully scheduled ${data.jobs_created} message${data.jobs_created > 1 ? 's' : ''}!`);
        showScreen('dashboard');
        document.getElementById('task-text').value = '';
        document.getElementById('proceed-schedule').disabled = true;
    });
    
    state.socket.on('schedule_failed', (data) => {
        console.error('❌ Schedule failed:', data);
        alert(`Failed to schedule: ${data.error}`);
    });
    
    state.socket.on('agent_disconnected', () => {
        console.log('🔌 Agent disconnected');
        updateAgentStatus(false);
    });
    
    state.socket.on('disconnect', () => {
        console.log('❌ Socket disconnected from server');
    });
    
    state.socket.on('error', (error) => {
        console.error('🚨 Socket error:', error);
    });
}

// Screen navigation
function showScreen(screenName) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    const screen = document.getElementById(`${screenName}-screen`);
    if (screen) {
        screen.classList.add('active');
        state.currentScreen = screenName;
    }
}

// Authentication
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            state.user = data.user;
            connectSocket();
            showScreen('dashboard');
            updateAgentStatus();
        } else {
            alert('Invalid credentials');
        }
    } catch (error) {
        console.error('Login error:', error);
        alert('Login failed');
    }
});

// Signup removed - single user system

// Navigation removed - single user system

document.getElementById('logout-btn').addEventListener('click', async () => {
    await fetch('/auth/logout', { method: 'POST' });
    state.user = null;
    if (state.socket) {
        state.socket.disconnect();
    }
    showScreen('login');
});

// Dashboard actions
document.getElementById('create-task-card').addEventListener('click', () => {
    showScreen('create-task');
});

document.getElementById('mission-control-card').addEventListener('click', () => {
    showScreen('mission-control');
    loadMissionControl();
});

document.getElementById('saved-messages-card').addEventListener('click', () => {
    showScreen('saved-messages');
    loadSavedMessages();
});

// Back buttons
document.querySelectorAll('.back-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const target = btn.getAttribute('data-target');
        showScreen(target);
    });
});

// Recording functionality
const recordBtn = document.getElementById('record-btn');
const recordText = recordBtn.querySelector('.record-text');
const recordingIndicator = document.querySelector('.recording-indicator');

recordBtn.addEventListener('click', async () => {
    // Check if browser speech recognition is available
    const hasBrowserSpeech = ('webkitSpeechRecognition' in window) || ('SpeechRecognition' in window);
    console.log('🎙️ Browser speech recognition available:', hasBrowserSpeech);
    
    if (hasBrowserSpeech) {
        // Use browser-based speech recognition
        console.log('🌐 Using browser-based speech recognition');
        window.startBrowserSpeechRecognition();
    } else {
        // Fall back to server-based recording
        if (!state.mediaRecorder) {
            // Start recording
            console.log('🎤 Starting audio recording (server-based)...');
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                console.log('✅ Microphone access granted');
                console.log('🎵 Audio stream:', stream);
                state.mediaRecorder = new MediaRecorder(stream);
                state.audioChunks = [];
                
                state.mediaRecorder.ondataavailable = (event) => {
                    console.log('📦 Audio chunk received, size:', event.data.size);
                    state.audioChunks.push(event.data);
                };
                
                state.mediaRecorder.onstop = async () => {
                    console.log('🛑 Recording stopped');
                    console.log('📦 Total chunks:', state.audioChunks.length);
                    const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
                    console.log('🎙️ Audio blob created, size:', audioBlob.size, 'type:', audioBlob.type);
                    await processAudio(audioBlob);
                };
                
                state.mediaRecorder.start();
                console.log('✅ MediaRecorder started');
                recordBtn.classList.add('recording');
                recordText.textContent = 'Stop Recording';
                recordingIndicator.style.display = 'flex';
                
            } catch (error) {
                console.error('❌ Recording error:', error);
                console.error('Error details:', error.message, error.stack);
                alert('Could not access microphone: ' + error.message);
            }
        } else {
            // Stop recording
            console.log('🛑 Stopping recording...');
            state.mediaRecorder.stop();
            state.mediaRecorder.stream.getTracks().forEach(track => {
                console.log('🔇 Stopping audio track:', track.label);
                track.stop();
            });
            state.mediaRecorder = null;
            
            recordBtn.classList.remove('recording');
            recordText.textContent = 'Start Recording';
            recordingIndicator.style.display = 'none';
        }
    }
});

async function processAudio(audioBlob) {
    console.log('🎙️ Processing audio blob...');
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    
    try {
        const response = await fetch('/api/speech-to-task', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('task-text').value = data.transcribed_text;
            document.getElementById('proceed-schedule').disabled = false;
            state.currentTask = data;
        } else {
            const errorData = await response.json();
            alert('Failed to transcribe audio: ' + (errorData.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Failed to process audio. Please try again.');
    }
}

// Task text input
document.getElementById('task-text').addEventListener('input', (e) => {
    document.getElementById('proceed-schedule').disabled = !e.target.value.trim();
});

// Proceed to schedule
document.getElementById('proceed-schedule').addEventListener('click', () => {
    const taskText = document.getElementById('task-text').value.trim();
    if (taskText) {
        state.currentTask = { transcribed_text: taskText };
        showScreen('schedule');
        updateWindowsList();
    }
});

// Schedule type selection
document.querySelectorAll('input[name="schedule-type"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
        const sequenceBuilder = document.getElementById('sequence-builder');
        if (e.target.value === 'sequence') {
            sequenceBuilder.style.display = 'block';
            updateSequenceSteps();
        } else {
            sequenceBuilder.style.display = 'none';
        }
    });
});

// Repetitions change
document.getElementById('repetitions').addEventListener('change', updateSequenceSteps);

function updateSequenceSteps() {
    const repetitions = parseInt(document.getElementById('repetitions').value);
    const stepsContainer = document.getElementById('sequence-steps');
    stepsContainer.innerHTML = '';
    
    for (let i = 1; i <= repetitions; i++) {
        const step = document.createElement('div');
        step.className = 'sequence-step';
        
        const content = i === 1 ? state.currentTask.transcribed_text : '';
        
        step.innerHTML = `
            <div class="step-number">Step ${i}:</div>
            <div class="step-content">
                <div class="step-preview">${content || '(Empty)'}</div>
                <div class="step-actions">
                    <button onclick="editStep(${i})">Type New</button>
                    <button onclick="loadFromSaved(${i})">Load Saved</button>
                </div>
            </div>
        `;
        
        stepsContainer.appendChild(step);
    }
}

// Submit schedule
document.getElementById('submit-schedule').addEventListener('click', async () => {
    console.log('📅 Submit schedule clicked');
    const scheduleType = document.querySelector('input[name="schedule-type"]:checked').value;
    const targetWindowSelect = document.getElementById('target-window');
    const targetWindow = targetWindowSelect.value;
    const startTime = document.getElementById('start-time').value;
    const repetitions = parseInt(document.getElementById('repetitions').value);
    const intervalValue = parseInt(document.getElementById('interval-value').value);
    const intervalUnit = document.getElementById('interval-unit').value;
    
    console.log('📋 Schedule data:', {
        scheduleType, targetWindow, startTime, repetitions, intervalValue, intervalUnit
    });
    console.log('🪟 Selected window option:', targetWindowSelect.selectedIndex, 'value:', targetWindow);
    console.log('🪟 Window dropdown HTML:', targetWindowSelect.innerHTML);
    
    if (!targetWindow || !startTime) {
        console.error('❌ Validation failed - targetWindow:', targetWindow, 'startTime:', startTime);
        alert('Please fill in all required fields');
        return;
    }
    
    // Convert interval to seconds
    let intervalSeconds = intervalValue;
    if (intervalUnit === 'minutes') intervalSeconds *= 60;
    if (intervalUnit === 'hours') intervalSeconds *= 3600;
    
    const scheduleData = {
        target_hwnd: parseInt(targetWindow),
        target_title: state.windows.find(w => w.hwnd == targetWindow)?.title || '',
        start_time: new Date(startTime).toISOString(),
        repetitions: repetitions,
        interval_seconds: intervalSeconds,
        use_different_messages: scheduleType === 'sequence'
    };
    
    if (scheduleType === 'sequence') {
        // Collect messages from sequence steps
        const messages = [];
        const steps = document.querySelectorAll('.sequence-step');
        for (let i = 0; i < repetitions; i++) {
            const preview = steps[i].querySelector('.step-preview').textContent;
            if (!preview || preview === '(Empty)') {
                alert(`Please fill in all sequence steps`);
                return;
            }
            messages.push(preview);
        }
        scheduleData.messages = messages;
    } else {
        scheduleData.message = state.currentTask.transcribed_text;
    }
    
    try {
        console.log('🚀 Sending schedule request:', scheduleData);
        const response = await fetch('/api/schedule', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(scheduleData)
        });
        console.log('📡 Schedule response:', response.status, response.statusText);
        
        if (response.ok) {
            const result = await response.json();
            console.log('✅ Schedule successful:', result);
            alert('Task scheduled successfully!');
            showScreen('dashboard');
            // Clear form
            document.getElementById('task-text').value = '';
            document.getElementById('proceed-schedule').disabled = true;
        } else {
            const errorText = await response.text();
            console.error('❌ Failed to schedule:', response.status, errorText);
            alert('Failed to schedule task');
        }
    } catch (error) {
        console.error('❌ Schedule error:', error);
        console.error('Error details:', error.message, error.stack);
        alert('Failed to schedule task: ' + error.message);
    }
});

// Window management
function updateWindowsList() {
    const select = document.getElementById('target-window');
    select.innerHTML = '<option value="">Select a window...</option>';
    
    state.windows.forEach(window => {
        const option = document.createElement('option');
        option.value = window.hwnd;
        option.textContent = window.title || `Window ${window.hwnd}`;
        select.appendChild(option);
    });
}

// Agent status
async function updateAgentStatus(online = null) {
    const statusElement = document.getElementById('agent-status');
    
    if (online === null) {
        // Check agent status
        try {
            const response = await fetch('/auth/agents');
            if (response.ok) {
                const agents = await response.json();
                online = agents.some(agent => agent.is_online);
            }
        } catch (error) {
            console.error('Agent status error:', error);
        }
    }
    
    if (online) {
        statusElement.textContent = 'Agent Online';
        statusElement.classList.remove('offline');
        statusElement.classList.add('online');
    } else {
        statusElement.textContent = 'Agent Offline';
        statusElement.classList.remove('online');
        statusElement.classList.add('offline');
    }
}

// Mission Control
async function loadMissionControl() {
    try {
        const response = await fetch('/api/jobs');
        if (response.ok) {
            const jobGroups = await response.json();
            displayJobGroups(jobGroups);
        }
    } catch (error) {
        console.error('Load jobs error:', error);
    }
}

function displayJobGroups(jobGroups) {
    const jobList = document.getElementById('job-list');
    jobList.innerHTML = '';
    
    if (jobGroups.length === 0) {
        jobList.innerHTML = '<p style="text-align: center; padding: 2rem;">No scheduled jobs</p>';
        return;
    }
    
    jobGroups.forEach(group => {
        const groupElement = document.createElement('div');
        groupElement.className = 'job-group';
        
        const pendingCount = group.jobs.filter(j => j.status === 'PENDING').length;
        const totalCount = group.jobs.length;
        
        groupElement.innerHTML = `
            <div class="job-group-header" onclick="toggleJobGroup(this)">
                <div>
                    <strong>${group.target_title || 'Window ' + group.target_hwnd}</strong>
                    <span style="margin-left: 1rem;">${pendingCount}/${totalCount} pending</span>
                </div>
                <span>▼</span>
            </div>
            <div class="job-details">
                ${group.jobs.map(job => `
                    <div class="job-item">
                        <div class="job-info">
                            <div>${job.message_text.substring(0, 50)}${job.message_text.length > 50 ? '...' : ''}</div>
                            <small>${new Date(job.scheduled_time).toLocaleString()}</small>
                        </div>
                        <span class="job-status ${job.status.toLowerCase()}">${job.status}</span>
                        ${job.status === 'PENDING' ? `
                            <div class="job-actions">
                                <button onclick="editJob(${job.id})">✏️</button>
                                <button onclick="rescheduleJob(${job.id})">🕐</button>
                                <button onclick="cancelJob(${job.id})">❌</button>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
        
        jobList.appendChild(groupElement);
    });
}

function toggleJobGroup(header) {
    header.parentElement.classList.toggle('expanded');
    const arrow = header.querySelector('span:last-child');
    arrow.textContent = header.parentElement.classList.contains('expanded') ? '▲' : '▼';
}

// Job actions
async function editJob(jobId) {
    const modal = document.getElementById('edit-modal');
    const textarea = document.getElementById('edit-message-text');
    const windowSelect = document.getElementById('edit-target-window');
    
    // Clear and populate window dropdown
    windowSelect.innerHTML = '<option value="">Select a window...</option>';
    state.windows.forEach(window => {
        const option = document.createElement('option');
        option.value = window.hwnd;
        option.textContent = window.title || `Window ${window.hwnd}`;
        windowSelect.appendChild(option);
    });
    
    // Get current job details
    try {
        const response = await fetch('/api/jobs');
        if (response.ok) {
            const jobGroups = await response.json();
            let job = null;
            let jobGroup = null;
            
            for (const group of jobGroups) {
                job = group.jobs.find(j => j.id === jobId);
                if (job) {
                    jobGroup = group;
                    break;
                }
            }
            
            if (job) {
                textarea.value = job.message_text;
                windowSelect.value = jobGroup.target_hwnd;
                modal.classList.add('active');
                
                // Save handler
                const saveHandler = async () => {
                    const updateData = {
                        message_text: textarea.value
                    };
                    
                    // Only include window update if changed
                    if (windowSelect.value && windowSelect.value != jobGroup.target_hwnd) {
                        updateData.target_hwnd = parseInt(windowSelect.value);
                        updateData.target_title = state.windows.find(w => w.hwnd == windowSelect.value)?.title || '';
                    }
                    
                    try {
                        const response = await fetch(`/api/jobs/${jobId}`, {
                            method: 'PUT',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(updateData)
                        });
                        
                        if (response.ok) {
                            modal.classList.remove('active');
                            loadMissionControl();
                        } else {
                            alert('Failed to update job');
                        }
                    } catch (error) {
                        console.error('Update error:', error);
                        alert('Failed to update job');
                    }
                };
                
                modal.querySelector('.save-btn').onclick = saveHandler;
                modal.querySelector('.cancel-btn').onclick = () => modal.classList.remove('active');
            }
        }
    } catch (error) {
        console.error('Load job error:', error);
    }
}

async function rescheduleJob(jobId) {
    const modal = document.getElementById('reschedule-modal');
    const input = document.getElementById('reschedule-time');
    
    modal.classList.add('active');
    
    const saveHandler = async () => {
        if (!input.value) {
            alert('Please select a new time');
            return;
        }
        
        try {
            const response = await fetch(`/api/jobs/${jobId}/reschedule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_scheduled_time: new Date(input.value).toISOString() })
            });
            
            if (response.ok) {
                modal.classList.remove('active');
                loadMissionControl();
            } else {
                alert('Failed to reschedule job');
            }
        } catch (error) {
            console.error('Reschedule error:', error);
            alert('Failed to reschedule job');
        }
    };
    
    modal.querySelector('.save-btn').onclick = saveHandler;
    modal.querySelector('.cancel-btn').onclick = () => modal.classList.remove('active');
}

async function cancelJob(jobId) {
    if (!confirm('Are you sure you want to cancel this job?')) return;
    
    try {
        const response = await fetch(`/api/jobs/${jobId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadMissionControl();
        } else {
            alert('Failed to cancel job');
        }
    } catch (error) {
        console.error('Cancel error:', error);
        alert('Failed to cancel job');
    }
}

// Saved messages
async function loadSavedMessages() {
    try {
        const response = await fetch('/api/tasks');
        if (response.ok) {
            const tasks = await response.json();
            displaySavedMessages(tasks);
        }
    } catch (error) {
        console.error('Load messages error:', error);
    }
}

function displaySavedMessages(tasks) {
    const messageList = document.getElementById('message-list');
    messageList.innerHTML = '';
    
    if (tasks.length === 0) {
        messageList.innerHTML = '<p style="text-align: center; padding: 2rem;">No saved messages</p>';
        return;
    }
    
    tasks.forEach(task => {
        const messageElement = document.createElement('div');
        messageElement.className = 'saved-message';
        messageElement.style.cssText = `
            padding: 1rem;
            margin-bottom: 0.5rem;
            background-color: var(--secondary-color);
            border-radius: 6px;
            cursor: pointer;
        `;
        
        messageElement.innerHTML = `
            <div>${task.text}</div>
            <small style="opacity: 0.7;">${new Date(task.created_at).toLocaleString()}</small>
        `;
        
        messageElement.addEventListener('click', () => {
            if (window.currentStepToFill) {
                fillSequenceStep(window.currentStepToFill, task.text);
                window.currentStepToFill = null;
            }
        });
        
        messageList.appendChild(messageElement);
    });
}

// Sequence builder helpers
window.editStep = function(stepNumber) {
    const step = document.querySelectorAll('.sequence-step')[stepNumber - 1];
    const preview = step.querySelector('.step-preview');
    
    const text = prompt('Enter message for this step:', preview.textContent === '(Empty)' ? '' : preview.textContent);
    if (text !== null && text.trim()) {
        preview.textContent = text;
    }
};

window.loadFromSaved = function(stepNumber) {
    window.currentStepToFill = stepNumber;
    showScreen('saved-messages');
    loadSavedMessages();
};

function fillSequenceStep(stepNumber, text) {
    const step = document.querySelectorAll('.sequence-step')[stepNumber - 1];
    const preview = step.querySelector('.step-preview');
    preview.textContent = text;
    showScreen('schedule');
}

// Rate limit banner
function showRateLimitBanner(resetTime) {
    const banner = document.getElementById('rate-limit-banner');
    const resetTimeElement = document.getElementById('reset-time');
    
    resetTimeElement.textContent = new Date(resetTime).toLocaleTimeString();
    banner.style.display = 'block';
    
    setTimeout(() => {
        banner.style.display = 'none';
    }, 30000); // Hide after 30 seconds
}

// Message search
document.getElementById('message-search').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const messages = document.querySelectorAll('.saved-message');
    
    messages.forEach(message => {
        const text = message.textContent.toLowerCase();
        message.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
});

// Message notification function
function showMessageNotification(message) {
    console.log('🔔 Showing notification:', message);
    
    // Request notification permission if not granted
    if ('Notification' in window && Notification.permission === 'default') {
        console.log('📱 Requesting notification permission...');
        Notification.requestPermission();
    }
    
    // Show browser notification if permitted
    if ('Notification' in window && Notification.permission === 'granted') {
        console.log('📱 Creating browser notification');
        const notification = new Notification('RemScheduler', {
            body: message,
            icon: '/favicon.ico',
            badge: '/favicon.ico',
            vibrate: [200, 100, 200]
        });
        
        // Close after 5 seconds
        setTimeout(() => notification.close(), 5000);
    }
    
    // Show in-app notification
    const notificationDiv = document.createElement('div');
    notificationDiv.className = 'notification-popup';
    notificationDiv.textContent = message;
    notificationDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: var(--success-color);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 255, 136, 0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease-out;
    `;
    
    document.body.appendChild(notificationDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notificationDiv.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notificationDiv.remove(), 300);
    }, 5000);
}

// Check authentication on load
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/auth/me');
        if (response.ok) {
            state.user = await response.json();
            connectSocket();
            showScreen('dashboard');
            updateAgentStatus();
            
            // Request notification permission on load
            if ('Notification' in window && Notification.permission === 'default') {
                console.log('📱 Requesting notification permission on load...');
                Notification.requestPermission();
            }
        }
    } catch (error) {
        console.error('Auth check error:', error);
    }
});