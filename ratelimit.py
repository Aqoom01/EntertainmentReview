from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import aioredis

async def init_limiter():
    redis = await aioredis.create_redis_pool("redis://localhost")
    await FastAPILimiter.init(redis)

def rate_limit(times: int, seconds: int):
    return RateLimiter(times=times, seconds=seconds)