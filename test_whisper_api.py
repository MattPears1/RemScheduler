#!/usr/bin/env python3
"""Test script to verify OpenAI Whisper API connectivity"""

import os
import sys
import requests
from openai import OpenAI

def test_api_key():
    """Test if API key is configured"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY environment variable found")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...{api_key[-4:]}")
    return True

def test_openai_connection():
    """Test basic OpenAI connectivity"""
    try:
        client = OpenAI()
        models = client.models.list()
        model_count = len(list(models))
        print(f"✅ Connected to OpenAI successfully (found {model_count} models)")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to OpenAI: {type(e).__name__}: {str(e)}")
        return False

def test_whisper_with_sample():
    """Test Whisper with a tiny sample audio file"""
    try:
        import tempfile
        import wave
        import struct
        
        # Create a tiny WAV file with silence
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            # WAV parameters
            channels = 1
            sample_width = 2
            framerate = 16000
            n_frames = 16000  # 1 second of audio
            
            # Create WAV file
            with wave.open(tmp.name, 'w') as wav:
                wav.setnchannels(channels)
                wav.setsampwidth(sample_width)
                wav.setframerate(framerate)
                
                # Write 1 second of silence
                for _ in range(n_frames):
                    wav.writeframes(struct.pack('<h', 0))
            
            # Test transcription
            client = OpenAI()
            print("📤 Sending test audio to Whisper API...")
            
            with open(tmp.name, 'rb') as audio_file:
                result = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            print(f"✅ Whisper API working! Result: '{result.text}' (empty is expected for silence)")
            
            # Clean up
            os.unlink(tmp.name)
            return True
            
    except Exception as e:
        print(f"❌ Whisper test failed: {type(e).__name__}: {str(e)}")
        return False

def test_heroku_endpoint():
    """Test the Heroku endpoint directly"""
    base_url = "https://remscheduler-ca6ac87d3a1a.herokuapp.com"
    
    # Test ping endpoint
    try:
        response = requests.get(f"{base_url}/api/ping", timeout=5)
        if response.ok:
            print(f"✅ Heroku ping endpoint working: {response.json()}")
        else:
            print(f"❌ Heroku ping endpoint returned {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to reach Heroku: {str(e)}")
    
    # Test API key configuration
    try:
        response = requests.get(f"{base_url}/api/test-api-key", timeout=5)
        if response.ok:
            data = response.json()
            if data['status'] == 'configured':
                print(f"✅ Heroku has API key configured: {data['key']}")
            else:
                print("❌ Heroku does NOT have API key configured")
    except Exception as e:
        print(f"❌ Failed to check Heroku API key: {str(e)}")

def main():
    print("🔍 Testing OpenAI Whisper API Configuration\n")
    
    # Run tests
    tests = [
        ("API Key Configuration", test_api_key),
        ("OpenAI Connection", test_openai_connection),
        ("Whisper API", test_whisper_with_sample),
        ("Heroku Endpoints", test_heroku_endpoint),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testing {name}...")
        print("-" * 40)
        success = test_func()
        results.append((name, success))
        print()
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 40)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
    
    # Overall result
    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed! Whisper API should work.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()