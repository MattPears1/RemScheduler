#!/usr/bin/env python3
"""Test Whisper API directly to see if it works"""

import os
import sys
import struct
import io

def create_test_wav():
    """Create a minimal WAV file with 1 second of silence"""
    sample_rate = 16000
    duration = 1
    samples = sample_rate * duration
    
    # Create WAV file in memory
    wav_file = io.BytesIO()
    
    # WAV header
    wav_file.write(b'RIFF')
    wav_file.write(struct.pack('<I', 36 + samples * 2))
    wav_file.write(b'WAVE')
    wav_file.write(b'fmt ')
    wav_file.write(struct.pack('<I', 16))
    wav_file.write(struct.pack('<H', 1))  # PCM
    wav_file.write(struct.pack('<H', 1))  # Mono
    wav_file.write(struct.pack('<I', sample_rate))
    wav_file.write(struct.pack('<I', sample_rate * 2))
    wav_file.write(struct.pack('<H', 2))
    wav_file.write(struct.pack('<H', 16))
    wav_file.write(b'data')
    wav_file.write(struct.pack('<I', samples * 2))
    
    # Write silence
    for _ in range(samples):
        wav_file.write(struct.pack('<h', 0))
    
    wav_file.seek(0)
    return wav_file

def test_openai_whisper():
    """Test OpenAI Whisper API"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("No OPENAI_API_KEY found")
        return False
    
    print(f"API Key found: {api_key[:10]}...")
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        print("OpenAI client created")
        
        # Create test audio
        audio_file = create_test_wav()
        audio_file.name = 'test.wav'
        
        print("Calling Whisper API...")
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
        
        print(f"Success! Transcription: '{transcript.text}'")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set the API key from command line if provided
    if len(sys.argv) > 1:
        os.environ['OPENAI_API_KEY'] = sys.argv[1]
    
    success = test_openai_whisper()
    sys.exit(0 if success else 1)