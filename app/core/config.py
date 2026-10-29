from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Document Intelligence & Editor"
    database_url: str = "sqlite:///./document_intelligence.db"
    cors_origins: list[str] = Field(default_factory=list)
    llm_provider: str = "mock"
    llm_model: str = "mock-v1"
    openai_api_key: str | None = None
    embedding_model: str = "hashing-v1"
    mock_mode: bool = True
    max_upload_size_mb: int = Field(default=10, gt=0)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
