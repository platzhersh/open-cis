from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    debug: bool = False
    cors_origins: list[str] = [
        "http://localhost:5173",
        "https://open-cis-web-staging.up.railway.app",
    ]

    # Database (Prisma)
    database_url: str = "postgresql://cis:cis@localhost:5432/cis"

    # EHRBase
    ehrbase_url: str = "http://localhost:8080/ehrbase/rest"
    ehrbase_user: str | None = None
    ehrbase_password: str | None = None

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars not in Settings


settings = Settings()
