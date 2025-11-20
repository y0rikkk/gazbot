"""Common schemas."""

from typing import Any
from pydantic import BaseModel, Field


class ResponseBase(BaseModel):
    """Базовая схема ответа API."""

    success: bool = True
    message: str | None = None
    data: Any | None = None


class ErrorResponse(BaseModel):
    """Схема ошибки."""

    success: bool = False
    message: str
    detail: str | None = None


class PaginationParams(BaseModel):
    """Параметры пагинации."""

    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class PaginatedResponse(BaseModel):
    """Схема ответа с пагинацией."""

    success: bool = True
    total: int
    skip: int
    limit: int
    data: list[Any]
