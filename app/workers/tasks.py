# Celeryタスク

from celery import Celery
import asyncio
from app.core.config import settings
from app.services.summarizer import summarize_content
from app.utils.cache import set_cache

celery_app = Celery(
    "summary_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# タスク実行
@celery_app.task(name="tasks.summarize")
def summarize_task(content: str, summary_level: str):
    result = asyncio.run(summarize_content(content, summary_level))
    
    # task_idをキーに結果をRedisに保存
    cache_key = f"task:{summarize_task.request.id}"
    asyncio.run(set_cache(cache_key, result))
    
    return {"task_id": summarize_task.request.id}