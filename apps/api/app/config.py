from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://narocatalog:narocatalog@localhost:5432/narocatalog"
    data_dir: str = "./data"
    private_artifact_dir: str = "./private_artifacts"
    adaptation_assets_root: str = ""
    adaptation_ephemeral_ttl_default_seconds: int = 3600
    adaptation_email_budget_bytes: int = 15 * 1024 * 1024
    adaptation_archive_soft_warn_bytes: int = 50 * 1024 * 1024
    max_source_document_bytes: int = 100 * 1024 * 1024
    max_source_document_pages: int = 500
    cors_origins: str = "*"
    app_version: str = "0.1.0"
    pdf_export_engine: str = "auto"
    pdf_api_base: str = "http://127.0.0.1:8000"


settings = Settings()
