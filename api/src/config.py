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

    # EHRBase (oehrpy client configuration)
    ehrbase_url: str = "http://localhost:8080/ehrbase"
    ehrbase_user: str | None = None
    ehrbase_password: str | None = None
    ehrbase_timeout: float = 30.0
    ehrbase_verify_ssl: bool = True

    # Terminology server (Snowstorm Lite)
    terminology_server_url: str = "http://localhost:8081/fhir"
    terminology_server_timeout: float = 30.0
    terminology_cache_ttl: int = 300
    terminology_validation_mode: str = "warn"  # strict | warn | off

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars not in Settings


settings = Settings()
