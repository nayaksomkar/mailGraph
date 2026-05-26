# Application configuration loaded from .env via pydantic-settings

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    # MongoDB connection string
    MONGODB_URI: str = "mongodb://localhost:27017/mailgraph"

    # Gmail proxy (Node.js Express server)
    GMAIL_PROXY_URL: str = "http://localhost:3000"

    # LLM API keys (only one provider is used at a time)
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""

    # LLM configuration
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.7

    # LangGraph workflow limits
    MAX_ITERATIONS: int = 3
    CRITIQUE_THRESHOLD: int = 8

    # FastAPI secret key for sessions/JWT
    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
