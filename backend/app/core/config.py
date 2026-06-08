import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.DATABASE_URL: str = os.environ["DATABASE_URL"]
        self.SECRET_KEY: str = os.environ["SECRET_KEY"]
        self.ALGORITHM: str = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
