"""Registration schemas."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.user import User
from app.schemas.event import Event
from app.schemas.user import UserUpdate


class RegistrationBase(BaseModel):
    """Базовая схема регистрации."""

    event_id: int = Field(..., gt=0)


class RegistrationCreate(RegistrationBase):
    """Схема для создания регистрации."""

    pass


class RegistrationInDB(RegistrationBase):
    """Схема регистрации из БД."""

    id: int
    user_id: int
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Registration(RegistrationInDB):
    """Схема регистрации для ответа API."""

    pass


class RegistrationWithDetails(Registration):
    """Схема регистрации с деталями пользователя и события."""

    user: User | None = None
    event: Event | None = None


class EventRegistrationRequest(BaseModel):
    """Схема для регистрации на мероприятие."""

    telegram_id: int
    user_data: UserUpdate
