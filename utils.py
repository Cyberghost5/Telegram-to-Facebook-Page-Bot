import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry(max_retries: int = 3, initial_delay: float = 2.0, backoff_factor: float = 2.0):
    """
    A decorator to retry a synchronous function with exponential backoff.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(
                            f"Attempt {attempt}/{max_retries} failed for {func.__name__}. "
                            f"No more retries left. Error: {e}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt}/{max_retries} failed for {func.__name__}. "
                        f"Retrying in {delay}s... Error: {e}"
                    )
                    time.sleep(delay)
                    delay *= backoff_factor
            return None  # Should not be reached because of raise in last attempt
        return wrapper
    return decorator
