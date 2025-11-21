"""Admin routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.registration import (
    RegistrationWithUserDetails,
    BulkUpdateStatusRequest,
    RegistrationStatusEnum,
)
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
    - status: Фильтр по статусу (pending, accepted, declined)
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
    - status: Новый статус (pending, accepted, declined)
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
