from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    HF_TOKEN: str | None = None

    MBART_MODEL_PATH: str = "model_unarchived/mbart_pos"
    MBART_SRC_LANG: str = "ru_RU"
    MBART_MAX_INPUT_LENGTH: int = 256
    MBART_MAX_NEW_TOKENS: int = 256
    MBART_NUM_BEAMS: int = 5

    CHUNK_CHARS: int = 800
    CHUNK_OVERLAP_CHARS: int = 100
    MAX_CHUNKS_PER_FILE: int = 100
    MAX_FILE_BYTES: int = 50 * 1024 * 1024

    BACKEND_URL: str = "backend url"

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
