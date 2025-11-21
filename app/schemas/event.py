"""Event schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class EventBase(BaseModel):
    """Базовая схема мероприятия."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    event_date: datetime
    location: str | None = Field(None, max_length=255)
    deadline: datetime
    is_active: bool = False


class EventCreate(EventBase):
    """Схема для создания мероприятия."""

    pass


class EventUpdate(BaseModel):
    """Схема для обновления мероприятия."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    event_date: datetime | None = None
    location: str | None = Field(None, max_length=255)
    deadline: datetime | None = None
    is_active: bool | None = None


class EventInDB(EventBase):
    """Схема мероприятия из БД."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Event(EventInDB):
    """Схема мероприятия для ответа API."""

    pass
