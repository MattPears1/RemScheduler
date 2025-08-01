"""
OpenAI helper module to handle client initialization
"""
import os
import logging

logger = logging.getLogger(__name__)

# Global client instance
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client"""
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment")
        return None
    
    try:
        from openai import OpenAI
        
        # Create client with just API key - let OpenAI handle the HTTP client
        # This is the simplest approach that should work on Heroku
        _openai_client = OpenAI(
            api_key=api_key,
            max_retries=2  # Retry failed requests up to 2 times
        )
        
        logger.info("OpenAI client initialized successfully")
        return _openai_client
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def transcribe_audio_with_fallback(audio_file_path):
    """Transcribe audio with multiple fallback options"""
    client = get_openai_client()
    if not client:
        logger.error("No OpenAI client available")
        return None
    
    try:
        # Method 1: Direct transcription
        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="en"
            )
            return transcript.text
    except Exception as e:
        logger.error(f"Direct transcription failed: {e}")
        
        # Method 2: Try with custom timeout
        try:
            import httpx
            from openai import OpenAI
            
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=30.0),
                verify=True,
                follow_redirects=True
            )
            
            temp_client = OpenAI(
                api_key=os.environ.get('OPENAI_API_KEY'),
                http_client=http_client
            )
            
            with open(audio_file_path, 'rb') as audio_file:
                transcript = temp_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
                http_client.close()
                return transcript.text
        except Exception as e2:
            logger.error(f"Fallback transcription also failed: {e2}")
            return None