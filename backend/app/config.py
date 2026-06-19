from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/rumors"
    anthropic_api_key: str = ""
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 1 week

    # Model IDs — only place these strings appear in the codebase
    extraction_model: str = "claude-haiku-4-5"
    synthesis_model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"


settings = Settings()
