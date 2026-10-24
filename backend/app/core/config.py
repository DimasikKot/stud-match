from pydantic_settings import BaseSettings
from functools import lru_cache


class _Settings(BaseSettings):
    REDIS_HOST: str
    REDIS_PORT: int

    DB_HOST: str
    DB_PORT: int
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_NAME: str

    USER_JWT_ACCESS_TOKEN_SECRET: str
    USER_JWT_ACCESS_TOKEN_EXPIRATION_HOURS: int
    USER_JWT_REFRESH_TOKEN_SECRET: str
    USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS: int

    TRAIN_JWT_ACCESS_TOKEN_SECRET: str

    STORAGE_PATH: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env.local"


@lru_cache
def __get_settings__():
    return _Settings()


settings: _Settings = __get_settings__()
