import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from app.core.llm_client import generate_summary

# テストケース: generate_summary関数の動作確認
@patch("app.core.llm_client.client.chat.completions.create", new_callable=AsyncMock)
def test_generate_summary(mock_create):
    mock_create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="- 要約結果")
            )
        ],
        usage=SimpleNamespace(total_tokens=42),
    )

    result = asyncio.run(generate_summary("本文の内容", "medium"))

    mock_create.assert_awaited_once()
    
    request = mock_create.await_args.kwargs
    
    assert request["model"] == "gpt-4o-mini"
    assert request["temperature"] == 0.2
    assert request["messages"][0] == {
        "role": "system",
        "content": "あなたは優秀な要約アシスタントです。",
    }
    assert request["messages"][1]["role"] == "user"
    assert "summary_level: medium" in request["messages"][1]["content"]
    assert "本文の内容" in request["messages"][1]["content"]
    assert result == {
        "summary": "- 要約結果",
        "tokens_used": 42,
        "model": "gpt-4o-mini",
    }