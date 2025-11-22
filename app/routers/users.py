"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import User, UserUpdate
from app.schemas.event import Event
from app.schemas.common import ResponseBase
from app.services import user_crud, registration_crud, event_crud
from app.models import event as event_model
from app.core.auth import CurrentUser

router = APIRouter()


@router.get(
    "/me",
    response_model=User,
    responses={
        200: {
            "description": "Профиль пользователя получен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "telegram_id": 123456789,
                        "telegram_username": "john_doe",
                        "first_name": "Иван",
                        "last_name": "Иванов",
                        "phone": "+79991234567",
                        "isu": 123456,
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован - отсутствует или невалидный X-Telegram-Init-Data",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        404: {
            "description": "Пользователь не найден в базе данных",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "User with telegram_id 123456789 not found in database"
                    }
                }
            },
        },
    },
)
def get_current_user_profile(user: CurrentUser):
    """
    Получить профиль текущего пользователя.

    **Требует аутентификации через Telegram Mini App.**

    Автоматически определяет пользователя из заголовка `X-Telegram-Init-Data`.
    Возвращает все данные профиля пользователя.
    """
    return user


@router.put(
    "/me",
    response_model=User,
    responses={
        200: {
            "description": "Профиль успешно обновлен",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "telegram_id": 123456789,
                        "telegram_username": "john_doe",
                        "first_name": "Иван",
                        "last_name": "Иванов",
                        "phone": "+79991234567",
                        "isu": 123456,
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
        500: {
            "description": "Ошибка при обновлении профиля",
            "content": {
                "application/json": {"example": {"detail": "Failed to update user"}}
            },
        },
    },
)
def update_current_user_profile(
    user_update: UserUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    """
    Обновить профиль текущего пользователя.

    **Требует аутентификации через Telegram Mini App.**

    Можно обновить следующие поля:
    - `first_name` - Имя
    - `last_name` - Фамилия
    - `phone` - Номер телефона
    - `isu` - ИСУ

    Все поля опциональны - обновляются только переданные поля.
    """
    updated_user = user_crud.update_user(db, user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )
    return updated_user


@router.get(
    "/me/events",
    response_model=list[Event],
    responses={
        200: {
            "description": "Список мероприятий пользователя",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "title": "Встреча с Газпромом",
                            "description": "Ежегодная встреча",
                            "event_date": "2025-12-15T18:00:00",
                            "location": "Офис Газпрома",
                            "deadline": "2025-12-10T23:59:59",
                            "is_active": False,
                            "created_at": "2025-11-20T10:00:00",
                            "updated_at": "2025-11-20T10:00:00",
                        }
                    ]
                }
            },
        },
        401: {
            "description": "Не авторизован",
            "content": {
                "application/json": {"example": {"detail": "Not authenticated"}}
            },
        },
    },
)
def get_my_events(
    user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Получить список мероприятий с принятыми регистрациями.

    **Требует аутентификации через Telegram Mini App.**

    Возвращает только те мероприятия, на которые регистрация пользователя
    была подтверждена (статус `accepted`).

    **Параметры пагинации:**
    - `skip` - сколько записей пропустить (default: 0)
    - `limit` - максимум записей вернуть (default: 100, max: 100)
    """
    events = event_crud.get_user_events(db, user.id, skip, limit)

    return events
