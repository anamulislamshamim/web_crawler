# API key authentication
from fastapi import Header, HTTPException, Security, Depends, Request
from fastapi.security.api_key import APIKeyHeader
from starlette import status as HttpStatus
import time
from settings import API_KEY_NAME


api_key_header = APIKeyHeader(name='x-api-key', auto_error=False)
# For demo purposes, we allow a single API key from env var; in prod use DB of keys.
ALLOWED_API_KEYS = set([API_KEY_NAME])

# Simple per-process in-memory rate limiter (not distributed). For distributed use Redis.
RATE_LIMIT = 100 # requests
RATE_PERIOD = 3600 # seconds

# store usage per key: {api_key: {'count': int, 'reset': timestamp}}
_usage_store = {}

async def get_api_key_header(api_key_header: str = Depends(api_key_header)):
    """Validate API key and enforce per-key rate limit (in-memory)."""
    if not api_key_header or api_key_header not in ALLOWED_API_KEYS:
        raise HTTPException(status_code=HttpStatus.HTTP_403_FORBIDDEN, detail='could not validate API key')
    
    # enforce rate limit
    now = int(time.time()) 
    record = _usage_store.get(api_key_header)
    if not record or now >= record['reset']:
        # initialize or reset period
        _usage_store[api_key_header] = {'count': 1, 'reset': now + RATE_PERIOD}
    else:
        if record['count'] >= RATE_LIMIT:
            # over limit 
            raise HTTPException(status_code=429, detail='Rate limit exceeded')
        record['count'] += 1
        _usage_store[api_key_header] = record 
    
    return api_key_header