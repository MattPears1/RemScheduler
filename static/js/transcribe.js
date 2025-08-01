// Alternative: Browser-based speech recognition
// This uses the Web Speech API for transcription instead of sending audio to server

let recognition = null;

function initSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        console.error('❌ Speech recognition not supported in this browser');
        return null;
    }
    
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    
    // Configure recognition
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;
    
    let finalTranscript = '';
    let interimTranscript = '';
    
    recognition.onresult = (event) => {
        interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            
            if (event.results[i].isFinal) {
                finalTranscript += transcript + ' ';
                console.log('✅ Final:', transcript);
            } else {
                interimTranscript += transcript;
                console.log('📝 Interim:', transcript);
            }
        }
        
        // Update the task text field with the current transcript
        const taskText = document.getElementById('task-text');
        if (taskText) {
            taskText.value = (finalTranscript + interimTranscript).trim();
        }
    };
    
    recognition.onerror = (event) => {
        console.error('❌ Speech recognition error:', event.error);
        if (event.error === 'no-speech') {
            console.log('🎤 No speech detected');
        }
    };
    
    recognition.onend = () => {
        console.log('🛑 Speech recognition ended');
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.classList.remove('recording');
            recordBtn.querySelector('.record-text').textContent = 'Start Recording';
        }
        
        // Enable proceed button if we have text
        const taskText = document.getElementById('task-text');
        const proceedBtn = document.getElementById('proceed-schedule');
        if (taskText && proceedBtn && taskText.value.trim()) {
            proceedBtn.disabled = false;
            console.log('✅ Transcription complete:', taskText.value);
        }
    };
    
    return recognition;
}

// Alternative recording function using Web Speech API
function startBrowserSpeechRecognition() {
    console.log('🎤 Starting browser-based speech recognition...');
    
    if (!recognition) {
        recognition = initSpeechRecognition();
        if (!recognition) {
            alert('Speech recognition is not supported in your browser. Please use Chrome or Edge.');
            return;
        }
    }
    
    const recordBtn = document.getElementById('record-btn');
    const recordText = recordBtn.querySelector('.record-text');
    const recordingIndicator = document.querySelector('.recording-indicator');
    
    if (recordBtn.classList.contains('recording')) {
        // Stop recording
        console.log('🛑 Stopping speech recognition...');
        recognition.stop();
        recordBtn.classList.remove('recording');
        recordText.textContent = 'Start Recording';
        recordingIndicator.style.display = 'none';
    } else {
        // Clear previous transcript
        document.getElementById('task-text').value = '';
        
        // Start recording
        recordBtn.classList.add('recording');
        recordText.textContent = 'Stop Recording';
        recordingIndicator.style.display = 'flex';
        
        try {
            recognition.start();
            console.log('✅ Speech recognition started');
        } catch (e) {
            console.error('❌ Failed to start speech recognition:', e);
            alert('Failed to start speech recognition. Please try again.');
            recordBtn.classList.remove('recording');
            recordText.textContent = 'Start Recording';
            recordingIndicator.style.display = 'none';
        }
    }
}

// Export for use in app.js
window.startBrowserSpeechRecognition = startBrowserSpeechRecognition;