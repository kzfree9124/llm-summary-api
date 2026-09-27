import io
from unittest.mock import AsyncMock, patch

def create_txt_file(content: str):
    return io.BytesIO(content.encode("utf-8"))

# region 正常系

# 要約処理テスト(同期処理)
@patch("app.api.summary.summarize_content", new_callable=AsyncMock)
def test_summary(mock_summarize_content, client):
    mock_summarize_content.return_value = {
        "summary": "要約結果です",
        "tokens_used": 123,
        "cached": False
    }
    
    file = ("test.txt", create_txt_file("これはテストです"), "text/plain")
    
    response = client.post(
        "/v1/summary",
        files={"file": file},
        params={"summary_level": "short", "async_process": False}
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["summary"] == "要約結果です"
    assert data["tokens_used"] == 123
    assert data["cached"] is False
    mock_summarize_content.assert_awaited_once_with("これはテストです", "short")

# 要約処理テスト(非同期処理)
@patch("app.api.summary.summarize_task.delay")
def test_summary_async(mock_delay, client):
    mock_delay.return_value.id = "task123"
    
    file = ("test.txt", create_txt_file("これはテストです"), "text/plain")
    
    response = client.post(
        "/v1/summary",
        files={"file": file},
        params={"summary_level": "short", "async_process": True}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["task_id"] == "task123"
    assert data["status"] == "processing"
    mock_delay.assert_called_once_with("これはテストです", "short")
    
# タスク結果をキャッシュから取得
@patch("app.api.summary.get_cache", new_callable=AsyncMock)
def test_get_summary_found(mock_get_cache, client):
    mock_get_cache.return_value = {
        "summary": "要約結果",
        "tokens_used": 123,
        "cached": False
    }
    
    response = client.get("/v1/summary/task123")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["result"]["summary"] == "要約結果"
    assert data["result"]["tokens_used"] == 123
    assert data["result"]["cached"] is False
    
# endregion

# region 異常系

# ファイルなし
def test_summary_no_file(client):
    response = client.post(
        "/v1/summary",
        params={"summary_level": "short", "async_process": False}
    )
    
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Field required"
    
# 要約レベルが不正
def test_summary_invalid_level(client):
    response = client.post(
        "/v1/summary",
        files={"file": ("test.txt", b"dummy", "text/plain")},
        params={"summary_level": "invalid", "async_process": False}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid summary_level."
    
# ファイル種別が不正
def test_summary_unsupported_file_type(client):
    response = client.post(
        "/v1/summary",
        files={"file": ("image.png", b"dummy", "image/png")},
        params={"summary_level": "short", "async_process": False}
    )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type."

# キャッシュに存在しないタスク結果を取得
@patch("app.api.summary.get_cache")
def test_get_summary_not_found(mock_get_cache, client):
    mock_get_cache.return_value = None
    
    response = client.get("/v1/summary/task999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Result not found."

# endregion