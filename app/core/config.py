from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Document Intelligence & Editor"
    database_url: str = "sqlite:///./document_intelligence.db"
    llm_provider: str = "mock"
    llm_model: str = "mock-v1"
    openai_api_key: str | None = None
    embedding_model: str = "hashing-v1"
    mock_mode: bool = True
    max_upload_size_mb: int = 10
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
