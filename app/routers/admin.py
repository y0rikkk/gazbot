"""Admin routes."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db

logger = logging.getLogger(__name__)
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
    responses={
        200: {
            "description": "Список регистраций с данными пользователей",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "user_id": 1,
                            "event_id": 1,
                            "status": "accepted",
                            "check_in_token": "abc123xyz",
                            "checked_in": True,
                            "checked_in_at": "2025-12-15T18:30:00",
                            "created_at": "2025-12-05T10:00:00",
                            "updated_at": "2025-12-15T18:30:00",
                            "user": {
                                "id": 1,
                                "telegram_id": 123456789,
                                "telegram_username": "john_doe",
                                "first_name": "Иван",
                                "last_name": "Иванов",
                                "phone": "+79991234567",
                                "isu": 123456,
                            },
                        }
                    ]
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
        404: {
            "description": "Мероприятие не найдено",
            "content": {"application/json": {"example": {"detail": "Event not found"}}},
        },
    },
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
        pattern="^(registered_at|name)$",
        description="Поле для сортировки: registered_at или name",
    ),
    sort_order: str = Query(
        "asc",
        pattern="^(asc|desc)$",
        description="Порядок сортировки: asc или desc",
    ),
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Получить список всех регистраций на мероприятие с информацией о пользователях.

    **Только для администраторов.**

    Возвращает полные данные о регистрациях включая информацию о пользователях,
    статус чек-ина и токен для QR-кода.

    **Параметры:**
    - `event_id` - ID мероприятия
    - `skip` - Количество записей для пропуска (пагинация)
    - `limit` - Максимальное количество записей (max: 1000)
    - `status` - Фильтр по статусу
    - `sort_by` - Сортировка по полю (registered_at, name)
    - `sort_order` - Порядок сортировки (asc, desc)
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


@router.post(
    "/registrations/bulk_update_statuses",
    response_model=ResponseBase,
    responses={
        200: {
            "description": "Статусы успешно обновлены",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Successfully updated 5 registration(s)",
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
        404: {
            "description": "Регистрации с указанными ID не найдены",
            "content": {
                "application/json": {
                    "example": {"detail": "No registrations found with provided IDs"}
                }
            },
        },
    },
)
def bulk_update_statuses(
    request: BulkUpdateStatusRequest,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Массово обновить статусы регистраций.

    **Только для администраторов.**

    Позволяет одновременно изменить статус для нескольких регистраций.
    Полезно для массового принятия/отклонения заявок.

    **Body:**
    - `registration_ids` - Список ID регистраций для обновления
    - `status` - Новый статус
    """
    # Обновляем статусы
    logger.info(
        f"Bulk status update: {len(request.registration_ids)} registrations "
        f"to status={request.status.value}"
    )
    updated_count = registration_crud.bulk_update_registration_statuses(
        db, request.registration_ids, request.status.value
    )

    if updated_count == 0:
        logger.warning(
            f"Bulk update failed: no registrations found for ids={request.registration_ids}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registrations found with provided IDs",
        )

    logger.info(f"Bulk update successful: {updated_count} registrations updated")
    return ResponseBase(
        success=True, message=f"Successfully updated {updated_count} registration(s)"
    )


@router.post(
    "/check-in",
    response_model=CheckInResponse,
    responses={
        200: {
            "description": "Пользователь успешно отмечен",
            "content": {
                "application/json": {
                    "examples": {
                        "new_checkin": {
                            "summary": "Новый чек-ин",
                            "value": {
                                "success": True,
                                "message": "Check-in successful",
                                "user": {
                                    "id": 1,
                                    "telegram_id": 123456789,
                                    "telegram_username": "john_doe",
                                    "first_name": "Иван",
                                    "last_name": "Иванов",
                                    "phone": "+79991234567",
                                    "isu": 123456,
                                },
                                "checked_in_at": "2025-12-15T18:30:00",
                            },
                        },
                        "already_checked": {
                            "summary": "Уже был отмечен ранее",
                            "value": {
                                "success": True,
                                "message": "User already checked in at 2025-12-15 18:30:00",
                                "user": {
                                    "id": 1,
                                    "telegram_id": 123456789,
                                    "telegram_username": "john_doe",
                                    "first_name": "Иван",
                                    "last_name": "Иванов",
                                    "phone": "+79991234567",
                                    "isu": 123456,
                                },
                                "checked_in_at": "2025-12-15T18:30:00",
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Регистрация не в статусе accepted",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Registration is not accepted. Current status: pending"
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
        404: {
            "description": "Регистрация не найдена по токену",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Registration not found. Invalid QR code token."
                    }
                }
            },
        },
    },
)
def check_in_user(
    request: CheckInRequest,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Отметить приход пользователя на мероприятие по QR-коду.

    **Только для администраторов.**

    Админ сканирует QR-код пользователя на фронтенде,
    извлекает `check_in_token` и отправляет его в этот эндпоинт.

    Система проверяет:
    1. Существует ли регистрация с таким токеном
    2. Имеет ли регистрация статус `accepted`
    3. Не был ли пользователь уже отмечен ранее

    Если пользователь уже был отмечен, возвращает время первого чек-ина.

    **Body:**
    - `token` - Токен из QR-кода (check_in_token)
    """
    # Находим регистрацию по токену
    logger.info(f"Check-in attempt with token: {request.token[:10]}...")
    registration = registration_crud.get_registration_by_token(db, request.token)

    if not registration:
        logger.warning(f"Check-in failed: Invalid token {request.token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found. Invalid QR code token.",
        )

    # Проверяем статус регистрации
    if registration.status != RegistrationStatusEnum.ACCEPTED:
        logger.warning(
            f"Check-in rejected: registration_id={registration.id}, "
            f"status={registration.status.value}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is not accepted. Current status: {registration.status.value}",
        )

    # Проверяем, не отмечен ли уже
    if registration.checked_in_at:
        logger.info(
            f"User already checked in: registration_id={registration.id}, "
            f"user={registration.user.telegram_username}"
        )
        return CheckInResponse(
            success=True,
            message=f"User already checked in at {registration.checked_in_at.strftime('%Y-%m-%d %H:%M:%S')}",
            user=registration.user,
            checked_in_at=registration.checked_in_at,
        )

    # Отмечаем как пришедшего
    registration = registration_crud.mark_checked_in(db, registration.id)
    logger.info(
        f"Check-in successful: registration_id={registration.id}, "
        f"user={registration.user.telegram_username or registration.user.telegram_id}"
    )

    return CheckInResponse(
        success=True,
        message="Check-in successful",
        user=registration.user,
        checked_in_at=registration.checked_in_at,
    )


@router.post(
    "/events",
    response_model=Event,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Мероприятие успешно создано",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Встреча с Газпромом",
                        "description": "Ежегодная встреча с партнерами",
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
        400: {
            "description": "Нельзя создать активное мероприятие - уже существует другое активное",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot create active event: another active event already exists. Please deactivate the current active event first."
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
    },
)
def create_event(
    event: EventCreate,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Создать новое мероприятие.

    **Только для администраторов.**

    **Ограничение:** В системе может быть только одно активное мероприятие.
    Если пытаетесь создать активное мероприятие при наличии другого активного - получите ошибку 400.

    **Body:**
    - `title` - Название мероприятия (обязательно)
    - `description` - Описание (обязательно)
    - `event_date` - Дата и время мероприятия (обязательно)
    - `location` - Место проведения (обязательно)
    - `deadline` - Крайний срок регистрации (обязательно)
    - `is_active` - Активно ли мероприятие (по умолчанию false)
    """
    logger.info(f"Creating event: {event.title}, active={event.is_active}")
    try:
        db_event = event_crud.create_event(db, event)
        logger.info(
            f"Event created successfully: id={db_event.id}, title={db_event.title}"
        )
        return db_event
    except IntegrityError as e:
        logger.error(f"Failed to create event: {event.title}, error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create active event: another active event already exists. Please deactivate the current active event first.",
        )


@router.get(
    "/events",
    response_model=list[Event],
    responses={
        200: {
            "description": "Список всех мероприятий",
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
                            "is_active": True,
                            "created_at": "2025-11-20T10:00:00",
                            "updated_at": "2025-11-20T10:00:00",
                        }
                    ]
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
    },
)
def get_all_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Получить список всех мероприятий.

    **Только для администраторов.**

    Возвращает все мероприятия (активные и неактивные) с пагинацией.

    **Параметры:**
    - `skip` - Количество записей для пропуска (default: 0)
    - `limit` - Максимальное количество записей (default: 100, max: 1000)
    """

    return event_crud.get_all_events(db, skip, limit)


@router.get(
    "/events/{event_id}",
    response_model=Event,
    responses={
        200: {
            "description": "Информация о мероприятии",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Встреча с Газпромом",
                        "description": "Ежегодная встреча",
                        "event_date": "2025-12-15T18:00:00",
                        "location": "Офис Газпрома",
                        "deadline": "2025-12-10T23:59:59",
                        "is_active": True,
                        "created_at": "2025-11-20T10:00:00",
                        "updated_at": "2025-11-20T10:00:00",
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
        404: {
            "description": "Мероприятие не найдено",
            "content": {"application/json": {"example": {"detail": "Event not found"}}},
        },
    },
)
def get_event(
    event_id: int,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Получить мероприятие по ID.

    **Только для администраторов.**

    **Параметры:**
    - `event_id` - ID мероприятия
    """
    event = event_crud.get_event_by_id(db, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return event


@router.put(
    "/events/{event_id}",
    response_model=Event,
    responses={
        200: {
            "description": "Мероприятие успешно обновлено",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "title": "Встреча с Газпромом (обновлено)",
                        "description": "Ежегодная встреча с партнерами",
                        "event_date": "2025-12-15T19:00:00",
                        "location": "Офис Газпрома",
                        "deadline": "2025-12-12T23:59:59",
                        "is_active": True,
                        "created_at": "2025-11-20T10:00:00",
                        "updated_at": "2025-11-25T14:30:00",
                    }
                }
            },
        },
        400: {
            "description": "Нельзя активировать мероприятие - уже есть другое активное",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cannot activate event: another active event already exists. Please deactivate the current active event first."
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
        404: {
            "description": "Мероприятие не найдено",
            "content": {"application/json": {"example": {"detail": "Event not found"}}},
        },
    },
)
def update_event(
    event_id: int,
    event_update: EventUpdate,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Обновить мероприятие.

    **Только для администраторов.**

    **Ограничение:** Нельзя активировать мероприятие, если уже есть другое активное.

    **Параметры:**
    - `event_id` - ID мероприятия

    **Body (все поля опциональны):**
    - `title` - Название мероприятия
    - `description` - Описание
    - `event_date` - Дата и время мероприятия
    - `location` - Место проведения
    - `deadline` - Крайний срок регистрации
    - `is_active` - Активно ли мероприятие
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


@router.delete(
    "/events/{event_id}",
    response_model=ResponseBase,
    responses={
        200: {
            "description": "Мероприятие успешно удалено",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Event deleted successfully",
                    }
                }
            },
        },
        401: {
            "description": "Не авторизован как администратор",
            "content": {
                "application/json": {
                    "example": {"detail": "Not authenticated as admin"}
                }
            },
        },
        404: {
            "description": "Мероприятие не найдено",
            "content": {"application/json": {"example": {"detail": "Event not found"}}},
        },
    },
)
def delete_event(
    event_id: int,
    admin: CurrentAdmin = None,
    db: Session = Depends(get_db),
):
    """
    Удалить мероприятие.

    **Только для администраторов.**

    **Внимание:** При удалении мероприятия также удаляются все связанные регистрации.

    **Параметры:**
    - `event_id` - ID мероприятия
    """
    success = event_crud.delete_event(db, event_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return ResponseBase(success=True, message="Event deleted successfully")
