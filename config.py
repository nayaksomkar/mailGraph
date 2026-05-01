from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "info"

    MONGODB_URI: str = "mongodb://localhost:27017/mailgraph"

    GMAIL_PROXY_URL: str = "http://localhost:3000"

    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    MISTRAL_API_KEY: str = ""

    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.1-8b-instant"
    LLM_TEMPERATURE: float = 0.7

    MAX_ITERATIONS: int = 3
    CRITIQUE_THRESHOLD: int = 8

    SECRET_KEY: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()