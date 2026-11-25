from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    HF_TOKEN: str | None = None

    BACKEND_URL: str = "backend url"

    # PLAINTEXT | SSL | SASL_SSL | SASL_PLAINTEXT; пусто = авто по порту
    KAFKA_SECURITY_PROTOCOL: str = ""
    KAFKA_SASL_MECHANISM: str = "PLAIN"
    KAFKA_SSL_CA_FILE: str = ""
    KAFKA_SSL_CHECK_HOSTNAME: bool = False

    KAFKA_HOST: str = "kafka host"
    KAFKA_PORT: int = 9900
    KAFKA_USERNAME: str = ""
    KAFKA_PASSWORD: str = ""

    KAFKA_TASKS_TOPIC: str = ""
    KAFKA_RESULTS_TOPIC: str = ""
    KAFKA_CONSUMER_GROUP: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def __get_settings__():
    return _Settings()


settings: _Settings = __get_settings__()
