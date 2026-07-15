import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class RetryPolicy:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

def with_retry(policy: RetryPolicy):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(policy.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < policy.max_retries:
                        delay = policy.base_delay * (2 ** attempt)
                        logger.warning(f"Error in {func.__name__}: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
            logger.error(f"Failed {func.__name__} after {policy.max_retries} retries.")
            raise last_exception
        return wrapper
    return decorator
