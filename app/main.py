# FastAPIエントリーポイント

from fastapi import FastAPI
from app.api.summary import router as summary_router
from app.api.health import router as health_router

app = FastAPI(title="AI Summary API")

app.include_router(summary_router, prefix="/v1")
app.include_router(health_router, prefix="/v1")