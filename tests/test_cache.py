import asyncio
import json
from unittest.mock import AsyncMock, patch
import pytest
from app.utils.cache import TTL_SECONDS, get_cache, set_cache

# region 正常系

# get_cacheテスト
@patch("app.utils.cache.redis.get", new_callable=AsyncMock)
def test_get_cache(mock_get):
    cached_value = {"summary": "要約", "tokens_used": 12}
    mock_get.return_value = json.dumps(cached_value)

    result = asyncio.run(get_cache("summary:key"))

    assert result == cached_value
    mock_get.assert_awaited_once_with("summary:key")
    
# set_cacheテスト
@patch("app.utils.cache.redis.set", new_callable=AsyncMock)
def test_set_cache(mock_set):
    value = {"summary": "要約", "tokens_used": 12}

    asyncio.run(set_cache("summary:key", value))

    mock_set.assert_awaited_once_with(
        "summary:key",
        json.dumps(value),
        ex=TTL_SECONDS,
    )
    assert TTL_SECONDS == 24 * 60 * 60

# endregion

# region 異常系

# キャッシュが存在しない場合、Noneを返す
@pytest.mark.parametrize("data", [None, ""])
@patch("app.utils.cache.redis.get", new_callable=AsyncMock)
def test_get_cache_returns_none_when_missing(mock_get, data):
    mock_get.return_value = data

    result = asyncio.run(get_cache("summary:key"))

    assert result is None
    mock_get.assert_awaited_once_with("summary:key")

# Redisの値が不正なJSONの場合、Noneを返す
@patch("app.utils.cache.redis.get", new_callable=AsyncMock)
def test_get_cache_returns_none_for_invalid_json(mock_get):
    mock_get.return_value = "{invalid json"

    result = asyncio.run(get_cache("summary:key"))

    assert result is None
    mock_get.assert_awaited_once_with("summary:key")

# endregion