"""Event routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas.event import Event, EventWithRegistrationCount
from app.schemas.registration import (
    Registration,
    RegistrationCreate,
    EventRegistrationRequest,
)
from app.schemas.common import ResponseBase
from app.services import event_crud, registration_crud, user_crud
from app.core.auth import CurrentUser

router = APIRouter()


@router.get("/", response_model=Event)
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


# @router.get("/", response_model=list[EventWithRegistrationCount])
# def get_events(
#     skip: int = Query(0, ge=0),
#     limit: int = Query(100, ge=1, le=1000),
#     active_only: bool = Query(
#         True, description="Показывать только активные мероприятия"
#     ),
#     db: Session = Depends(get_db),
# ):
#     """
#     Получить список мероприятий.

#     Параметры:
#     - skip: Количество записей для пропуска
#     - limit: Максимальное количество записей
#     - active_only: Только активные мероприятия (где deadline еще не истек)
#     """
#     if active_only:
#         events = event_crud.get_active_events(db, skip, limit)
#     else:
#         events = event_crud.get_all_events(db, skip, limit)

#     # Добавляем количество регистраций для каждого события
#     events_with_count = []
#     for event in events:
#         count = registration_crud.count_event_registrations(db, event.id)
#         event_dict = event.__dict__.copy()
#         event_dict["registrations_count"] = count
#         events_with_count.append(EventWithRegistrationCount(**event_dict))

#     return events_with_count


# @router.get("/{event_id}", response_model=EventWithRegistrationCount)
# def get_event(event_id: int, db: Session = Depends(get_db)):
#     """
#     Получить информацию о мероприятии.

#     Параметры:
#     - event_id: ID мероприятия
#     """
#     event = event_crud.get_event_by_id(db, event_id)
#     if not event:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
#         )

#     count = registration_crud.count_event_registrations(db, event.id)
#     event_dict = event.__dict__.copy()
#     event_dict["registrations_count"] = count

#     return EventWithRegistrationCount(**event_dict)


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
    if event.deadline < datetime.now() or not event.is_active:
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


# @router.delete("/{event_id}/register", response_model=ResponseBase)
# def unregister_from_event(
#     event_id: int, telegram_id: int, db: Session = Depends(get_db)
# ):
#     """
#     Отменить регистрацию на мероприятие.

#     Параметры:
#     - event_id: ID мероприятия
#     - telegram_id: ID пользователя в Telegram
#     """
#     # Проверяем существование пользователя
#     user = user_crud.get_user_by_telegram_id(db, telegram_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     # Проверяем существование регистрации
#     registration = registration_crud.get_user_registration(db, user.id, event_id)
#     if not registration:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found"
#         )

#     # Удаляем регистрацию
#     success = registration_crud.delete_registration(db, registration.id)
#     if not success:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to delete registration",
#         )

#     return ResponseBase(success=True, message="Registration cancelled successfully")
