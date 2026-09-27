# 要約API

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.file_parser import parse_file
from app.services.summarizer import summarize_content
from app.workers.tasks import summarize_task
from app.utils.cache import get_cache

router = APIRouter()

"""
要約API
- asyncio_process=false → 同期処理
- asyncio_process=true → Celeryで非同期処理
"""
@router.post("/summary")
async def create_summary(
    file: UploadFile = File(...),
    summary_level: str = "short",
    async_process: bool = False
):
    # テキスト抽出
    content = parse_file(file)
    
    # 非同期処理の場合
    if async_process:
        task = summarize_task.delay(content, summary_level)
        return {"task_id": task.id, "status": "processing"}
    
    # 同期処理の場合
    result = await summarize_content(content, summary_level)
    return result

# 非同期タスクの結果取得
@router.get("/summary/{task_id}")
async def get_summary_result(task_id: str):
    cache_key = f"task:{task_id}"
    result = await get_cache(cache_key)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found.")
    
    return {
        "task_id": task_id,
        "status": "completed",
        "result": result
    }