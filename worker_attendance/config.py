"""Loads environment configuration via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str = ""
    owner_chat_id: int = 0
    admin_password: str = ""
    tz: str = "Asia/Tbilisi"
    daily_send_time: str = "08:00"
    data_dir: str = "./data"
    admin_host: str = "0.0.0.0"
    admin_port: int = 8000
    bot_lang: str = "ka"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
