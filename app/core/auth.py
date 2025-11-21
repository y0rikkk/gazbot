"""Telegram Web App authentication utilities."""

import hmac
import hashlib
import json
import time
from typing import Annotated
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.services import user_crud
from app.schemas.user import UserCreate


def validate_init_data(init_data: str) -> dict:
    """
    Валидация Telegram Web App initData.

    Args:
        init_data: Строка initData из Telegram Web App

    Returns:
        dict: Распарсенные данные пользователя

    Raises:
        HTTPException: Если данные невалидны
    """
    try:
        # Парсим данные
        parsed_data = dict(parse_qsl(init_data))

        # Получаем hash
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            raise ValueError("Hash not found")

        # Создаем data_check_string (сортируем параметры по ключу)
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)

        # Вычисляем secret_key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.TELEGRAM_BOT_TOKEN.encode(),
            digestmod=hashlib.sha256,
        ).digest()

        # Вычисляем hash
        calculated_hash = hmac.new(
            key=secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256
        ).hexdigest()

        # Проверяем hash
        if not hmac.compare_digest(received_hash, calculated_hash):
            raise ValueError("Invalid hash")

        # Проверяем auth_date (данные не старше 24 часов)
        auth_date = int(parsed_data.get("auth_date", 0))
        current_time = int(time.time())
        if current_time - auth_date > 86400:  # 24 часа
            raise ValueError("Init data is too old")

        return parsed_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Telegram init data: {str(e)}",
        )


def get_current_user(
    x_telegram_init_data: Annotated[str, Header(alias="X-Telegram-Init-Data")],
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency для получения текущего пользователя из Telegram Web App.

    Автоматически:
    1. Валидирует initData
    2. Извлекает информацию о пользователе
    3. Создает пользователя в БД если его нет
    4. Возвращает объект User

    В DEV_MODE:
    - X-Telegram-Init-Data должен содержать только telegram_id
    - Пример: "123456789"
    - Валидация HMAC пропускается

    Args:
        x_telegram_init_data: initData из заголовка запроса
        db: Database session

    Returns:
        User: Объект пользователя из БД
    """

    if settings.DEV_MODE:
        try:
            telegram_id = int(x_telegram_init_data)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="In DEV_MODE, X-Telegram-Init-Data must be a valid telegram_id (integer)",
            )

        db_user = user_crud.get_user_by_telegram_id(db, telegram_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with telegram_id {telegram_id} not found in database",
            )

        return db_user

    # Валидируем initData
    parsed_data = validate_init_data(x_telegram_init_data)

    # Парсим данные пользователя
    user_data = json.loads(parsed_data.get("user", "{}"))

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in init data",
        )

    # Пытаемся найти пользователя в БД
    db_user = user_crud.get_user_by_telegram_id(db, telegram_id)

    # Если пользователя нет - создаем
    if not db_user:
        user_create = UserCreate(
            telegram_id=telegram_id,
            telegram_username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            phone=None,
            isu=None,
        )
        db_user = user_crud.create_user(db, user_create)

    return db_user


# Удобный alias для использования в роутерах
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_admin(current_user: CurrentUser) -> User:
    """
    Dependency для проверки, что текущий пользователь является администратором.

    Args:
        current_user: Текущий пользователь (автоматически из get_current_user)

    Returns:
        User: Объект пользователя-администратора

    Raises:
        HTTPException: Если пользователь не является администратором
    """
    if current_user.telegram_id not in settings.admin_ids_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Administrator privileges required.",
        )

    return current_user


# Удобный alias для использования в admin роутерах
CurrentAdmin = Annotated[User, Depends(get_current_admin)]
