"""Schemas package."""

from app.schemas.user import User, UserCreate, UserUpdate, UserInDB
from app.schemas.event import (
    Event,
    EventCreate,
    EventUpdate,
    EventInDB,
)
from app.schemas.registration import (
    Registration,
    RegistrationCreate,
    RegistrationInDB,
    RegistrationWithUserDetails,
)
from app.schemas.telegram import TelegramUser, TelegramWebAppData, MessageSend
from app.schemas.common import (
    ResponseBase,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
)

__all__ = [
    # User
    "User",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    # Event
    "Event",
    "EventCreate",
    "EventUpdate",
    "EventInDB",
    # Registration
    "Registration",
    "RegistrationCreate",
    "RegistrationInDB",
    "RegistrationWithUserDetails",
    # Telegram
    "TelegramUser",
    "TelegramWebAppData",
    "MessageSend",
    # Common
    "ResponseBase",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
]
