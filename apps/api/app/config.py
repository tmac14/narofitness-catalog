from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://narocatalog:narocatalog@localhost:5432/narocatalog"
    data_dir: str = "./data"
    cors_origins: str = "*"
    app_version: str = "0.1.0"
    pdf_export_engine: str = "auto"
    pdf_api_base: str = "http://127.0.0.1:8000"


settings = Settings()
