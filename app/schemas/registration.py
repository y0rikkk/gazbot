"""Registration schemas."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.user import User
from app.schemas.event import Event
from app.schemas.user import UserUpdate


class RegistrationStatusEnum(Enum):
    """Статус регистрации на мероприятие."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    PAYMENT = "payment"
    REJECTED = "rejected"


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
    status: RegistrationStatusEnum
    check_in_token: str
    checked_in_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class Registration(RegistrationInDB):
    """Схема регистрации для ответа API."""

    pass


class RegistrationWithUserDetails(Registration):
    """Схема регистрации с деталями пользователя."""

    user: User


class EventRegistrationRequest(BaseModel):
    """Схема для регистрации на мероприятие (только данные для обновления)."""

    user_data: UserUpdate


class BulkUpdateStatusRequest(BaseModel):
    """Схема для массового обновления статусов регистраций."""

    registration_ids: list[int] = Field(..., min_length=1)
    status: RegistrationStatusEnum


class CheckInRequest(BaseModel):
    """Схема для check-in запроса."""

    token: str = Field(..., min_length=1)


class CheckInResponse(BaseModel):
    """Схема для check-in ответа."""

    success: bool
    message: str
    user: User | None = None
    checked_in_at: datetime | None = None
