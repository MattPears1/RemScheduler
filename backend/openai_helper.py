"""
OpenAI helper module to handle client initialization with proxy workaround
"""
import os
import logging

logger = logging.getLogger(__name__)

# Global client instance
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client with proxy workaround"""
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logger.error("No OPENAI_API_KEY found in environment")
        return None
    
    try:
        # Import httpx first and configure it to not use proxies
        import httpx
        
        # Create a custom httpx client that explicitly disables proxies
        http_client = httpx.Client(
            proxies=None,  # Explicitly disable proxies
            trust_env=False,  # Don't trust environment proxy settings
            timeout=httpx.Timeout(30.0)
        )
        
        # Import OpenAI after httpx is configured
        from openai import OpenAI
        
        # Create client with custom http client
        _openai_client = OpenAI(
            api_key=api_key,
            http_client=http_client,
            max_retries=1
        )
        
        logger.info("OpenAI client initialized successfully with custom HTTP client")
        return _openai_client
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Try fallback method - clear environment and retry
        try:
            logger.info("Trying fallback method...")
            
            # Save current environment
            saved_env = os.environ.copy()
            
            # Clear proxy variables
            proxy_vars = [
                'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
            ]
            
            for var in proxy_vars:
                if var in os.environ:
                    del os.environ[var]
            
            # Import OpenAI in clean environment
            from openai import OpenAI
            
            # Create simple client
            _openai_client = OpenAI(api_key=api_key)
            
            # Restore environment
            os.environ.clear()
            os.environ.update(saved_env)
            
            logger.info("OpenAI client initialized with fallback method")
            return _openai_client
            
        except Exception as e2:
            logger.error(f"Fallback method also failed: {e2}")
            return None