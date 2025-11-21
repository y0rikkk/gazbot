"""Tests for authentication."""

import pytest
from fastapi import HTTPException

from app.core.auth import validate_init_data


def test_validate_init_data_missing_hash():
    """Тест с отсутствующим hash."""
    with pytest.raises(HTTPException) as exc_info:
        validate_init_data("auth_date=12345&user_id=123")

    assert exc_info.value.status_code == 401
    assert "Invalid Telegram init data" in str(exc_info.value.detail)


def test_validate_init_data_invalid_format():
    """Тест с невалидным форматом данных."""
    with pytest.raises(HTTPException) as exc_info:
        validate_init_data("invalid_data")

    assert exc_info.value.status_code == 401
