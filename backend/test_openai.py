"""
Test script to verify OpenAI connectivity on Heroku
"""
import os
import sys
import socket
import httpx
from openai import OpenAI

def test_dns_resolution():
    """Test DNS resolution for OpenAI API"""
    try:
        ip = socket.gethostbyname('api.openai.com')
        print(f"✅ DNS resolution successful: api.openai.com -> {ip}")
        return True
    except Exception as e:
        print(f"❌ DNS resolution failed: {e}")
        return False

def test_direct_https():
    """Test direct HTTPS connection"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get('https://api.openai.com/v1/models')
            print(f"✅ Direct HTTPS connection: Status {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ Direct HTTPS failed: {e}")
        return False

def test_openai_client():
    """Test OpenAI client initialization and simple API call"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY found")
        return False
    
    try:
        # Create minimal client
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client created")
        
        # Try a simple API call
        models = client.models.list()
        print(f"✅ API call successful, found {len(list(models))} models")
        return True
    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False

def test_minimal_transcription():
    """Test minimal transcription with a tiny audio file"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY for transcription test")
        return False
    
    try:
        import io
        import struct
        
        # Create a minimal WAV file (1 second of silence)
        sample_rate = 16000
        duration = 1
        samples = sample_rate * duration
        
        # WAV header
        wav_file = io.BytesIO()
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
        wav_file.name = 'test.wav'
        
        # Try transcription
        client = OpenAI(api_key=api_key)
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=wav_file,
            language="en"
        )
        print(f"✅ Transcription successful: '{transcript.text}'")
        return True
    except Exception as e:
        print(f"❌ Transcription test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=== OpenAI Connectivity Test ===")
    print(f"Python version: {sys.version}")
    print(f"OpenAI API Key present: {bool(os.environ.get('OPENAI_API_KEY'))}")
    print()
    
    # Run tests
    tests = [
        ("DNS Resolution", test_dns_resolution),
        ("Direct HTTPS", test_direct_https),
        ("OpenAI Client", test_openai_client),
        ("Minimal Transcription", test_minimal_transcription)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n--- {name} ---")
        results.append(test_func())
    
    print("\n=== Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)