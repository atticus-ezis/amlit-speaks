from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    use_supabase: bool
    openai_api_key: str
    supabase_service_role_key: str
    supabase_project_url: str
    elevenlabs_api_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings():
    return Settings()


settings = Settings()
