from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://evaluator:evaluator_dev@localhost:5434/evaluator"
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    HARNESS_API_URL: str = "https://api.harnessexchange.com"
    HARNESS_API_KEY: str = ""
    HARNESS_API_MOCK: bool = True
    EXPORT_API_KEY: str = "evaluator-export-key-dev"
    RESEND_API_KEY: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
