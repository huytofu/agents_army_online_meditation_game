from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    forest_database_url: str = (
        "postgresql+asyncpg://forest:forest@127.0.0.1:5436/meditation_forest"
    )
    forest_port: int = 8765
    world_seed: int = 20261105


def get_settings() -> Settings:
    return Settings()
