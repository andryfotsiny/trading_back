# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/trading_bot"
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    EXCHANGE_NAME: str = "binance"
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_TESTNET: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"

    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""

    AI_PROVIDER: str = "claude"
    CLAUDE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OLLAMA_MODEL: str = "deepseek-r1"

    class Config:
        env_file = ".env"


settings = Settings()
