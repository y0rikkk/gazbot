"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    """Базовая схема пользователя."""

    telegram_username: str = Field(..., min_length=1, max_length=255)
    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    isu: int | None = Field(
        None, ge=100000, le=999999, description="ИСУ номер (6 цифр)"
    )
    address: str | None = Field(None, max_length=500)


class UserCreate(UserBase):
    """Схема для создания пользователя."""

    telegram_id: int = Field(..., gt=0)


class UserUpdate(BaseModel):
    """Схема для обновления пользователя."""

    first_name: str | None = Field(None, max_length=255)
    last_name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    isu: int | None = Field(None, ge=100000, le=999999)
    address: str | None = Field(None, max_length=500)


class UserInDB(UserBase):
    """Схема пользователя из БД."""

    id: int
    telegram_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class User(UserInDB):
    """Схема пользователя для ответа API."""

    pass
