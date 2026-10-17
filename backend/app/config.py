from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


class Settings(BaseModel):
    gemini_api_key: str | None = Field(default=None)
    gemini_model: str = Field(default="gemma-3-27b-it")
    max_image_bytes: int = Field(default=10 * 1024 * 1024, gt=0)

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemma-3-27b-it"),
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_environment()
