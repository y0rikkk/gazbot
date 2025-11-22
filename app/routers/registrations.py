"""Registrations routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.registration import Registration, RegistrationStatusEnum
from app.services import event_crud, registration_crud
from app.core.auth import CurrentUser
from app.core.qr_code import generate_qr_code_image


router = APIRouter()


@router.get(
    "/my",
    response_model=Registration,
    responses={
        200: {
            "description": "Активная регистрация пользователя",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "event_id": 1,
                        "status": "accepted",
                        "check_in_token": "abc123xyz",
                        "checked_in": False,
                        "checked_in_at": None,
                        "created_at": "2025-12-05T10:00:00",
                        "updated_at": "2025-12-05T10:00:00",
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
            "description": "Активное мероприятие или регистрация не найдены",
            "content": {
                "application/json": {
                    "examples": {
                        "no_event": {
                            "summary": "Нет активного мероприятия",
                            "value": {"detail": "Active event not found"},
                        },
                        "no_registration": {
                            "summary": "Нет регистрации на активное мероприятие",
                            "value": {
                                "detail": "User registration for active event not found"
                            },
                        },
                    }
                }
            },
        },
    },
)
def get_user_current_registration(user: CurrentUser, db: Session = Depends(get_db)):
    """
    Получить активную регистрацию пользователя.

    **Требует аутентификации через Telegram Mini App.**

    Возвращает регистрацию пользователя на текущее активное мероприятие.
    Если активного мероприятия нет или пользователь не зарегистрирован - возвращает 404.

    """
    event = event_crud.get_active_event(db)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Active event not found"
        )
    user_registration = registration_crud.get_user_registration(db, user.id, event.id)
    if not user_registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User registration for active event not found",
        )
    return user_registration


@router.get(
    "/{registration_id}/qr-code",
    responses={
        200: {
            "description": "QR-код в формате PNG",
            "content": {
                "image/png": {"schema": {"type": "string", "format": "binary"}}
            },
        },
        400: {
            "description": "Регистрация не подтверждена",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Registration is not accepted. Current status: pending"
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
        403: {
            "description": "Регистрация принадлежит другому пользователю",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Access denied. This registration belongs to another user."
                    }
                }
            },
        },
        404: {
            "description": "Регистрация не найдена",
            "content": {
                "application/json": {"example": {"detail": "Registration not found"}}
            },
        },
    },
)
def get_registration_qr_code(
    registration_id: int,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Получить QR-код для регистрации (билет на мероприятие).

    **Требует аутентификации через Telegram Mini App.**

    QR-код содержит уникальный токен `check_in_token`, который можно отсканировать
    для отметки прихода на мероприятие.

    **Ограничения:**
    - Доступен только владельцу регистрации
    - Регистрация должна быть в статусе `accepted`

    **Параметры:**
    - `registration_id` - ID регистрации

    **Возвращает:** PNG изображение QR-кода размером 200x200 пикселей
    """
    # Получаем регистрацию
    registration = registration_crud.get_registration_by_id(db, registration_id)

    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found"
        )

    # Проверяем, что регистрация принадлежит текущему пользователю
    if registration.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This registration belongs to another user.",
        )

    # Проверяем статус регистрации
    if registration.status != RegistrationStatusEnum.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is not accepted. Current status: {registration.status.value}",
        )

    # Генерируем QR-код с токеном
    qr_code_image = generate_qr_code_image(registration.check_in_token)

    # Возвращаем изображение
    return Response(
        content=qr_code_image,
        media_type="image/png",
        headers={
            "Content-Disposition": f"inline; filename=ticket_{registration_id}.png"
        },
    )
