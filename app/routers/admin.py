"""Admin routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.schemas.registration import (
    RegistrationWithUserDetails,
    BulkUpdateStatusRequest,
    RegistrationStatusEnum,
    CheckInRequest,
    CheckInResponse,
)
from app.schemas.event import Event, EventCreate, EventUpdate
from app.schemas.common import ResponseBase
from app.services import registration_crud, event_crud
from app.core.auth import CurrentAdmin

router = APIRouter()


@router.get(
    "/events/{event_id}/registrations",
    response_model=list[RegistrationWithUserDetails],
)
def get_event_registrations(
    event_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    status: RegistrationStatusEnum | None = Query(
        None, description="Фильтр по статусу регистрации"
    ),
    sort_by: str = Query(
        "registered_at",
        regex="^(registered_at|name)$",
        description="Поле для сортировки: registered_at или name",
    ),
    sort_order: str = Query(
        "asc",
        regex="^(asc|desc)$",
        description="Порядок сортировки: asc или desc",
    ),
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Получить список всех регистраций на мероприятие с информацией о пользователях.

    Только для администраторов.

    Параметры:
    - event_id: ID мероприятия
    - skip: Количество записей для пропуска
    - limit: Максимальное количество записей
    - status: Фильтр по статусу (pending, accepted, declined, cancelled)
    - sort_by: Сортировка по полю (registered_at, name)
    - sort_order: Порядок сортировки (asc, desc)
    """
    # Проверяем существование события
    event = event_crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    # Получаем регистрации с данными пользователей
    registrations = registration_crud.get_event_registrations_with_users(
        db=db,
        event_id=event_id,
        skip=skip,
        limit=limit,
        status_filter=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return registrations


@router.post("/registrations/bulk_update_statuses", response_model=ResponseBase)
def bulk_update_statuses(
    request: BulkUpdateStatusRequest,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Массово обновить статусы регистраций.

    Только для администраторов.

    Body:
    - registration_ids: Список ID регистраций
    - status: Новый статус (pending, accepted, declined, cancelled)
    """
    # Обновляем статусы
    updated_count = registration_crud.bulk_update_registration_statuses(
        db, request.registration_ids, request.status.value
    )

    if updated_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registrations found with provided IDs",
        )

    return ResponseBase(
        success=True, message=f"Successfully updated {updated_count} registration(s)"
    )


@router.post("/check-in", response_model=CheckInResponse)
def check_in_user(
    request: CheckInRequest,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Отметить приход пользователя на мероприятие по QR-коду.

    Только для администраторов.

    Админ сканирует QR-код пользователя на фронтенде,
    извлекает токен и отправляет его сюда.

    Body:
    - token: Токен из QR-кода
    """
    # Находим регистрацию по токену
    registration = registration_crud.get_registration_by_token(db, request.token)

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found. Invalid QR code token.",
        )

    # Проверяем статус регистрации
    if registration.status != RegistrationStatusEnum.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is not accepted. Current status: {registration.status.value}",
        )

    # Проверяем, не отмечен ли уже
    if registration.checked_in_at:
        return CheckInResponse(
            success=True,
            message=f"User already checked in at {registration.checked_in_at.strftime('%Y-%m-%d %H:%M:%S')}",
            user=registration.user,
            checked_in_at=registration.checked_in_at,
        )

    # Отмечаем как пришедшего
    registration = registration_crud.mark_checked_in(db, registration.id)

    return CheckInResponse(
        success=True,
        message="Check-in successful",
        user=registration.user,
        checked_in_at=registration.checked_in_at,
    )


@router.post("/events", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(
    event: EventCreate,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Создать новое мероприятие.

    Только для администраторов.

    Body:
    - title: Название мероприятия
    - description: Описание
    - event_date: Дата и время мероприятия
    - location: Место проведения
    - deadline: Крайний срок регистрации
    - is_active: Активно ли мероприятие (по умолчанию false)
    """
    try:
        db_event = event_crud.create_event(db, event)
        return db_event
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create active event: another active event already exists. Please deactivate the current active event first.",
        )


@router.get("/events", response_model=list[Event])
def get_all_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Получить список всех мероприятий.

    Только для администраторов.

    Параметры:
    - skip: Количество записей для пропуска
    - limit: Максимальное количество записей
    """

    return event_crud.get_all_events(db, skip, limit)


@router.get("/events/{event_id}", response_model=Event)
def get_event(
    event_id: int,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Получить мероприятие по ID.

    Только для администраторов.

    Параметры:
    - event_id: ID мероприятия
    """
    event = event_crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.put("/events/{event_id}", response_model=Event)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Обновить мероприятие.

    Только для администраторов.

    Параметры:
    - event_id: ID мероприятия

    Body:
    - title: Название мероприятия (опционально)
    - description: Описание (опционально)
    - event_date: Дата и время мероприятия (опционально)
    - location: Место проведения (опционально)
    - deadline: Крайний срок регистрации (опционально)
    - is_active: Активно ли мероприятие (опционально)
    """
    try:
        db_event = event_crud.update_event(db, event_id, event_update)
        if not db_event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
            )
        return db_event
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot activate event: another active event already exists. Please deactivate the current active event first.",
        )


@router.delete("/events/{event_id}", response_model=ResponseBase)
def delete_event(
    event_id: int,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Удалить мероприятие.

    Только для администраторов.

    Параметры:
    - event_id: ID мероприятия
    """
    success = event_crud.delete_event(db, event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return ResponseBase(success=True, message="Event deleted successfully")
