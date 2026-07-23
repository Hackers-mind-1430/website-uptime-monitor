from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Uptime Monitor"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./uptime_monitor.db"

    class Config:
        env_file = ".env"


settings = Settings()
