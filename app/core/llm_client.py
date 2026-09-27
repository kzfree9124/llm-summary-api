# LLM呼び出しクライアント

from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def generate_summary(content: str, summary_level: str) -> dict:
    prompt = f"""
    あなたは企業向けのドキュメント要約アシスタントです。
    以下の文章を、指定された粒度で要約してください。
    
    - summary_level: {summary_level}
    - 出力形式： 箇条書き
    - 重要ポイントを優先
    - 数値・固有名詞は保持
    
    本文：
    {content}
    """
    
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたは優秀な要約アシスタントです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    return {
        "summary": response.choices[0].message.content,
        "tokens_used": response.usage.total_tokens,
        "model": "gpt-4o-mini"
    }