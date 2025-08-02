import asyncio
from functools import wraps

from loguru import logger

class RetryOverException(Exception):
     pass

def retry(max_retries: int = 1, delay: float = 1.0):
    """
    异步函数重试装饰器。

    :param max_retries: 最大重试次数
    :param delay: 每次重试之间的延迟时间（单位：秒）
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except RetryOverException:
                    raise
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Error {repr(e)} . Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        raise RetryOverException(f"Error {repr(e)} . Attempt {attempt + 1} failed. No more retries.") from e
            return None

        return wrapper
    return decorator