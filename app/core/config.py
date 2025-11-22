"""Application configuration using pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "GazBot API"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_BOT_USERNAME: str

    # Admin Users (список telegram_id администраторов через запятую)
    ADMIN_TELEGRAM_IDS: str = ""

    # Development mode (skip Telegram auth validation)
    DEV_MODE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @property
    def admin_ids_list(self) -> list[int]:
        """Преобразует строку admin ids в список int."""
        if not self.ADMIN_TELEGRAM_IDS:
            return []
        return [
            int(id_.strip())
            for id_ in self.ADMIN_TELEGRAM_IDS.split(",")
            if id_.strip()
        ]


settings = Settings()
