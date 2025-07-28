# utils/retries.py
import time
from functools import wraps

def retry(max_tentativas=3, delay=2, exceptions=(Exception,)):
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tentativa = 1
            while tentativa <= max_tentativas:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"Tentativa {tentativa} falhou: {e}")
                    if tentativa == max_tentativas:
                        raise
                    time.sleep(delay)
                    tentativa += 1
        return wrapper
    return decorator_retry
