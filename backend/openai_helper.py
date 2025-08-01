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
        import httpx
        
        # Create a custom httpx client with better timeout settings
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),  # 60s total, 10s connect
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            follow_redirects=True
        )
        
        # Create client with API key and custom http client
        _openai_client = OpenAI(
            api_key=api_key,
            http_client=http_client,
            max_retries=2  # Retry failed requests up to 2 times
        )
        
        logger.info("OpenAI client initialized successfully with custom timeout settings")
        return _openai_client
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None