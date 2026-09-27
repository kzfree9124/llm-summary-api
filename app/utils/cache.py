# Redisキャッシュ

import json
from redis.asyncio import Redis

# Redis接続(接続プール)
redis = Redis(
    host="redis",
    port=6379,
    db=0,
    decode_responses=True
)

TTL_SECONDS = 60 * 60 * 24  # 24時間

# Redisキャッシュから取得
async def get_cache(key: str):
    data = await redis.get(key)
    if not data:
        return None
    
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None
    
# Redisにキャッシュ保存
async def set_cache(key: str, value: dict):
    await redis.set(key, json.dumps(value), ex=TTL_SECONDS)