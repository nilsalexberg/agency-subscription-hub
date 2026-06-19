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
        self.EFI_CLIENT_ID: str = os.environ["EFI_CLIENT_ID"]
        self.EFI_CLIENT_SECRET: str = os.environ["EFI_CLIENT_SECRET"]
        self.EFI_SANDBOX: bool = os.getenv("EFI_SANDBOX", "true").lower() in (
            "1",
            "true",
            "yes",
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
