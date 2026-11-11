from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class _Settings(BaseSettings):
    VITE_BACKEND_URL: str = "backend host"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6300
    REDIS_PASSWORD: str = "password"

    POSTGRES_HOST: str = "postgres host"
    POSTGRES_PORT: int = 5400
    POSTGRES_SSLMODE: str = "allow"
    POSTGRES_DB: str = "name db"
    POSTGRES_USER: str = "name user"
    POSTGRES_PASSWORD: str = "password"

    USER_JWT_ACCESS_TOKEN_SECRET: str = "w3NWlz4BSf6j6TwwEEXK0pT5yPY4AJzt"
    USER_JWT_ACCESS_TOKEN_EXPIRATION_HOURS: int = 1
    USER_JWT_REFRESH_TOKEN_SECRET: str = "v4m9mCNqrIjiNdYiarb4SwUBH5mxCe4O"
    USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS: int = 720

    COOKIE_HTTPONLY: bool = True
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: str = "lax"

    RUSTFS_URL: str = "rustfs host"
    RUSTFS_BUCKET: str = "bucket"
    RUSTFS_ACCESS_KEY: str = "user"
    RUSTFS_SECRET_KEY: str = "password"
    RUSTFS_REGION: str = "ru-central1"

    KAFKA_HOST: str = "kafka host"
    KAFKA_PORT: int = 9900
    KAFKA_USERNAME: str = ""
    KAFKA_PASSWORD: str = ""

    # PLAINTEXT | SSL | SASL_SSL | SASL_PLAINTEXT; пусто = авто по порту
    KAFKA_SECURITY_PROTOCOL: str = ""
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_SSL_CA_FILE: str = ""
    KAFKA_SSL_CHECK_HOSTNAME: bool = False
    KAFKA_RESULTS_GROUP_ID: str = "sm-backend-llm-results"

    LLM_MAX_FILES_CHARS: int = 12000  # ~8k токенов контекста влезает в 4 ГБ VRAM

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}?sslmode={self.POSTGRES_SSLMODE}"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def __get_settings__():
    return _Settings()


settings: _Settings = __get_settings__()
