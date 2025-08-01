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
        
        # Create client with API key
        _openai_client = OpenAI(api_key=api_key)
        
        logger.info("OpenAI client initialized successfully")
        return _openai_client
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None