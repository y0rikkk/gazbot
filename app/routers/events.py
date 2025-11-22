"""Event routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.event import Event
from app.schemas.registration import (
    Registration,
    RegistrationCreate,
    EventRegistrationRequest,
)
from app.services import event_crud, registration_crud, user_crud
from app.core.auth import CurrentUser

router = APIRouter()


@router.get(
    "/current",
    response_model=Event,
    responses={
        200: {
            "description": "Активное мероприятие найдено",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Встреча с Газпромом",
                        "description": "Ежегодная встреча сотрудников",
                        "event_date": "2025-12-15T18:00:00",
                        "location": "Офис Газпрома, Москва",
                        "deadline": "2025-12-10T23:59:59",
                        "is_active": True,
                        "created_at": "2025-11-20T10:00:00",
                        "updated_at": "2025-11-20T10:00:00",
                    }
                }
            },
        },
        404: {
            "description": "Активное мероприятие не найдено",
            "content": {
                "application/json": {"example": {"detail": "Active event not found"}}
            },
        },
    },
)
def get_current_event(
    db: Session = Depends(get_db),
):
    """
    Получить текущее активное мероприятие.

    Возвращает информацию о мероприятии, на которое можно зарегистрироваться.
    В системе может быть только одно активное мероприятие одновременно.
    """
    event = event_crud.get_active_event(db)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Active event not found"
        )
    return event


@router.post(
    "/{event_id}/register",
    response_model=Registration,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Регистрация успешно создана",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 123,
                        "event_id": 1,
                        "registered_at": "2025-11-22T14:30:00",
                        "status": "pending",
                        "check_in_token": "abc123def456",
                        "checked_in_at": None,
                    }
                }
            },
        },
        400: {
            "description": "Ошибка валидации или дедлайн истек",
            "content": {
                "application/json": {
                    "examples": {
                        "deadline_passed": {
                            "summary": "Дедлайн истек",
                            "value": {
                                "detail": "Registration deadline has passed or event is not active"
                            },
                        },
                        "already_registered": {
                            "summary": "Уже зарегистрирован",
                            "value": {"detail": "Already registered for this event"},
                        },
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
        404: {
            "description": "Мероприятие не найдено",
            "content": {"application/json": {"example": {"detail": "Event not found"}}},
        },
    },
)
def register_for_event(
    event_id: int,
    registration_request: EventRegistrationRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Зарегистрироваться на мероприятие.

    **Требует аутентификации через Telegram Mini App.**

    При регистрации:
    - Обновляются данные пользователя (имя, телефон, ису)
    - Создается регистрация со статусом "pending"
    - Генерируется уникальный токен для QR-кода

    **Ограничения:**
    - Нельзя зарегистрироваться после дедлайна
    - Нельзя зарегистрироваться дважды на одно мероприятие
    - Мероприятие должно быть активным
    """
    # Проверяем существование события
    event = event_crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Проверяем, не истек ли дедлайн регистрации и мероприятие активно
    if (
        event.deadline < datetime.now()
        or not event.is_active
        or event.event_date < datetime.now()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration deadline has passed or event is not active",
        )

    # Обновляем данные пользователя
    user_crud.update_user(db, user.id, registration_request.user_data)

    # Проверяем, не зарегистрирован ли уже пользователь
    existing_registration = registration_crud.get_user_registration(
        db, user.id, event_id
    )
    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already registered for this event",
        )

    # Создаем регистрацию
    registration_data = RegistrationCreate(event_id=event_id)
    registration = registration_crud.create_registration(db, user.id, registration_data)

    return registration
