# 要約ロジック

from app.core.llm_client import generate_summary
from app.utils.cache import get_cache, set_cache
from fastapi import HTTPException
import hashlib

# ファイル内容、要約レベルからキャッシュキーを生成
def generate_cache_key(content: str, summary_level: str) -> str:
    hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"summary:{hash_value}:{summary_level}"

# 要約処理のメインロジック
async def summarize_content(content: str, summary_level: str = "short") -> dict:
    if summary_level not in ["short", "medium", "long"]:
        raise HTTPException(status_code=400, detail="Invalid summary_level.")
    
    # キャッシュキー生成
    cache_key = generate_cache_key(content, summary_level)
    
    # キャッシュ確認
    cached = await get_cache(cache_key)
    
    if cached:
        return {
            "summary": cached["summary"],
            "tokens_used": cached["tokens_used"],
            "cached": True
        }
        
    # LLM呼び出し
    result = await generate_summary(content, summary_level)
    
    # キャッシュ保存
    await set_cache(cache_key, result)
    
    result["cached"] = False
    
    return result