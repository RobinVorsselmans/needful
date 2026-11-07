"""Instellingen uit omgevingsvariabelen of uit .env (sjabloon: .env.example)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore": .env bevat ook variabelen die de code (nog) niet leest, zoals DATABASE_URL
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-haiku-5.5"
