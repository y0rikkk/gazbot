"""Telegram Web App schemas."""

from pydantic import BaseModel, Field


class TelegramUser(BaseModel):
    """Схема пользователя из Telegram Web App initData."""

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None


class TelegramWebAppData(BaseModel):
    """Схема данных Telegram Web App."""

    query_id: str | None = None
    user: TelegramUser
    auth_date: int
    hash: str


class MessageSend(BaseModel):
    """Схема для отправки сообщения пользователю."""

    telegram_id: int = Field(..., gt=0)
    message: str = Field(..., min_length=1, max_length=4096)
