import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.workers.tasks import summarize_task

# タスクテスト
@patch("app.workers.tasks.summarize_content", new_callable=AsyncMock)
@patch("app.workers.tasks.set_cache", new_callable=AsyncMock)
def test_summarize_task(mock_set_cache, mock_summarize_content):
    summary_result = {
        "summary": "LLMの要約結果",
        "tokens_used": 123,
        "cached": False
    }
    mock_summarize_content.return_value = summary_result
    
    result = summarize_task.apply(
        args=("テスト内容", "short"),
        task_id="task123"
    ).get()
    
    assert result == {"task_id": "task123"}
    
    # LLMが呼ばれている
    mock_summarize_content.assert_awaited_once_with("テスト内容", "short")
    
    # Redisにキャッシュが保存されている
    mock_set_cache.assert_awaited_once()
    
    cache_key, cached_result = mock_set_cache.await_args.args
    assert cache_key == "task:task123"
    assert cached_result["summary"] == "LLMの要約結果"
    assert cached_result["tokens_used"] == 123
    assert cached_result["cached"] is False
    
def test_summarize_task_invalid_level():
    with pytest.raises(HTTPException) as exc:
        summarize_task.run("テスト内容", "unknown")
        
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid summary_level."