import asyncio
import random
import time
from typing import Callable, Any 
import re


async def retry_async(func: Callable, retries: int = 3, initial_delay: float = 0.5, backoff: float = 2.0, jitter: bool = True, *args, **kwargs):
    """Simple async retry with exponential backoff and optional jitter."""
    attempt = 0
    delay = initial_delay
    while True:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            attempt += 1
            if attempt > retries:
                raise 
            if jitter:
                sleep_time = delay + random.uniform(0, delay)
            else:
                sleep_time = delay
            
            await asyncio.sleep(sleep_time)
            delay *= backoff
            
# Small helper to parse price strings like '£51.77'
def parse_price(text: str):
    if not text:
        return None 
    
    m = re.search(r"([\d\.,]+)", text)
    
    if not m:
        return None 
    amount = m.group(1).replace(',', '')
    try:
        val = float(amount)
    except:
        val = None 
    
    # currency symbol
    currency = None 
    symbol = re.search(r"[^\d\s\.,]+", text)
    
    if symbol:
        currency = symbol.group(0)
    
    return {"amount": amount, "currency": currency}