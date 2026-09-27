import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from app.services.summarizer import summarize_content

# region 正常系

# キャッシュがある場合：LLMを呼ばない
@patch("app.services.summarizer.get_cache", new_callable=AsyncMock)
@patch("app.services.summarizer.generate_summary", new_callable=AsyncMock)
def test_summarizer_with_cache(mock_generate_summary, mock_get_cache):
    mock_get_cache.return_value = {
        "summary": "キャッシュされた要約",
        "tokens_used": 0,
        "cached": True
    }
    
    result = asyncio.run(summarize_content("テスト内容", "short"))
    
    assert result["summary"] == "キャッシュされた要約"
    assert result["cached"] is True
    
    # LLMは呼ばれていない
    mock_generate_summary.assert_not_called()
    
# キャッシュが無い場合：LLMを呼ぶ
@patch("app.services.summarizer.get_cache", new_callable=AsyncMock)
@patch("app.services.summarizer.generate_summary", new_callable=AsyncMock)
@patch("app.services.summarizer.set_cache", new_callable=AsyncMock)
def test_summarizer_without_cache(mock_set_cache, mock_generate_summary, mock_get_cache):
    mock_get_cache.return_value = None
    
    mock_generate_summary.return_value = {
        "summary": "LLMの要約結果",
        "tokens_used": 123,
        "cached": False
    }
    
    result = asyncio.run(summarize_content("テスト内容", "short"))
    
    assert result["summary"] == "LLMの要約結果"
    assert result["cached"] is False
    
    # LLMが呼ばれている
    mock_generate_summary.assert_called_once()
    
    # キャッシュが保存されている
    mock_set_cache.assert_called_once()
    
# endregion

# region 異常系

# 要約レベルが不正の場合
def test_summarizer_invalid_level():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(summarize_content("テスト内容", "unknown"))
        
    assert exc.value.status_code == 400
    assert exc.value.detail == "Invalid summary_level."
# endregion