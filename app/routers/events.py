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


@router.get("/current", response_model=Event)
def get_current_event(
    db: Session = Depends(get_db),
):
    """
    Получить активное мероприятие.

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
)
def register_for_event(
    event_id: int,
    registration_request: EventRegistrationRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Зарегистрироваться на мероприятие.

    Автоматически обновляет данные пользователя при регистрации.
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
