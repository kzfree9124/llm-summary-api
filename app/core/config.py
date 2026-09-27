# 設定(APIキー、環境変数)

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    REDIS_URL: str = "edis://redis:6379/0"
    
    model_config = ConfigDict(env_file=".env")

settings = Settings()