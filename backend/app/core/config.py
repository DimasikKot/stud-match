from pydantic_settings import BaseSettings
from functools import lru_cache


class _Settings(BaseSettings):
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    DB_HOST: str = "sm-postgres"
    DB_PORT: int = 5432
    DB_USERNAME: str = "sm_admin"
    DB_PASSWORD: str = "password_superPuper"
    DB_NAME: str = "stud-match"

    USER_JWT_ACCESS_TOKEN_SECRET: str = "w3NWlz4BSf6j6TwwEEXK0pT5yPY4AJzt"
    USER_JWT_ACCESS_TOKEN_EXPIRATION_HOURS: int = 1
    USER_JWT_REFRESH_TOKEN_SECRET: str = "v4m9mCNqrIjiNdYiarb4SwUBH5mxCe4O"
    USER_JWT_REFRESH_TOKEN_EXPIRATION_HOURS: int = 720

    TRAIN_JWT_ACCESS_TOKEN_SECRET: str = "r1yGRupzNCNGwEstj5fL0c5NFfjtON2B"

    STORAGE_PATH: str = "./files"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env.local"


@lru_cache
def __get_settings__():
    return _Settings()


settings: _Settings = __get_settings__()
