"""Registrations routes."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.registration import (
    Registration,
    RegistrationStatusEnum,
)
from app.services import event_crud, registration_crud
from app.core.auth import CurrentUser
from app.core.qr_code import generate_qr_code_image

logger = logging.getLogger(__name__)

router = APIRouter()

# Директория для хранения чеков
RECEIPTS_DIR = Path("receipts")
RECEIPTS_DIR.mkdir(exist_ok=True)

# Разрешенные форматы файлов
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


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


@router.post(
    "/{registration_id}/payment",
    responses={
        200: {
            "description": "Квитанция загружена, QR-код возвращен",
            "content": {
                "image/png": {"schema": {"type": "string", "format": "binary"}}
            },
        },
        400: {
            "description": "Некорректный статус регистрации или формат файла",
            "content": {
                "application/json": {
                    "examples": {
                        "wrong_status": {
                            "summary": "Регистрация не в статусе payment",
                            "value": {
                                "detail": "Registration is not in payment status. Current status: accepted"
                            },
                        },
                        "invalid_format": {
                            "summary": "Недопустимый формат файла",
                            "value": {
                                "detail": "Invalid file format. Allowed formats: .pdf, .jpg, .jpeg, .png"
                            },
                        },
                        "file_too_large": {
                            "summary": "Файл слишком большой",
                            "value": {"detail": "File size exceeds 10 MB limit"},
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
async def upload_payment(
    registration_id: int,
    user: CurrentUser,
    receipt: UploadFile = File(..., description="Квитанция об оплате (PDF, JPG, PNG)"),
    db: Session = Depends(get_db),
):
    """
    Загрузить квитанцию об оплате для регистрации.

    **Требует аутентификации через Telegram Mini App.**

    После успешной загрузки квитанции статус регистрации меняется на `accepted`
    и возвращается QR-код билета.

    **Ограничения:**
    - Доступен только владельцу регистрации
    - Регистрация должна быть в статусе `payment`
    - Допустимые форматы: PDF, JPG, JPEG, PNG
    - Максимальный размер файла: 10 MB

    **Параметры:**
    - `registration_id` - ID регистрации
    - `receipt` - Файл квитанции об оплате

    **Возвращает:** PNG изображение QR-кода билета размером 200x200 пикселей
    """
    logger.info(
        f"Payment upload attempt: registration_id={registration_id}, "
        f"filename={receipt.filename}, size={receipt.size or 'unknown'}"
    )

    # Получаем регистрацию
    registration = registration_crud.get_registration_by_id(db, registration_id)

    if not registration:
        logger.warning(
            f"Payment upload failed: Registration {registration_id} not found"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found"
        )

    # Проверяем, что регистрация принадлежит текущему пользователю
    if registration.user_id != user.id:
        logger.warning(
            f"Payment upload rejected: registration_id={registration_id} "
            f"belongs to user_id={registration.user_id}, not {user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This registration belongs to another user.",
        )

    # Проверяем статус регистрации
    if registration.status != RegistrationStatusEnum.PAYMENT:
        logger.warning(
            f"Payment upload rejected: registration_id={registration_id}, "
            f"status={registration.status.value} (expected: payment)"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is not in payment status. Current status: {registration.status.value}",
        )

    # Проверяем формат файла
    file_ext = Path(receipt.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        logger.warning(
            f"Payment upload rejected: registration_id={registration_id}, "
            f"invalid format={file_ext}, allowed={ALLOWED_EXTENSIONS}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Читаем содержимое файла и проверяем размер
    file_content = await receipt.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    if len(file_content) > MAX_FILE_SIZE:
        logger.warning(
            f"Payment upload rejected: registration_id={registration_id}, "
            f"file size {file_size_mb:.2f}MB exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB limit",
        )

    # Формируем имя файла: {last_name}_{first_name}_{telegram_username}_{registration_id}{ext}
    filename_parts = []
    if user.last_name:
        filename_parts.append(user.last_name)
    if user.first_name:
        filename_parts.append(user.first_name)
    if user.telegram_username:
        filename_parts.append(user.telegram_username)
    filename_parts.append(str(registration_id))

    filename = "_".join(filename_parts) + file_ext
    file_path = RECEIPTS_DIR / filename

    # Сохраняем файл
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(
            f"Payment receipt saved: registration_id={registration_id}, "
            f"filename={filename}, size={file_size_mb:.2f}MB"
        )
    except Exception as e:
        logger.error(
            f"Failed to save receipt: registration_id={registration_id}, "
            f"filename={filename}, error={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save receipt: {str(e)}",
        )

    # Обновляем статус регистрации на accepted
    registration.status = RegistrationStatusEnum.ACCEPTED
    db.commit()
    db.refresh(registration)

    logger.info(
        f"Payment upload successful: registration_id={registration_id}, "
        f"user={user.telegram_username or user.telegram_id}, "
        f"status changed to accepted"
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


@router.post(
    "/{registration_id}/decline",
    response_model=Registration,
    responses={
        200: {
            "description": "Регистрация отклонена пользователем",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 1,
                        "event_id": 1,
                        "status": "declined",
                        "check_in_token": "abc123xyz",
                        "checked_in": False,
                        "checked_in_at": None,
                        "created_at": "2025-12-05T10:00:00",
                        "updated_at": "2025-12-05T10:00:00",
                    }
                }
            },
        },
        400: {
            "description": "Регистрация не в статусе payment",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Registration is not in payment status. Current status: accepted"
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
def decline_payment(
    registration_id: int,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Отклонить оплату и отказаться от регистрации.

    **Требует аутентификации через Telegram Mini App.**

    Позволяет пользователю отказаться от оплаты и регистрации на мероприятие.
    Статус регистрации меняется на `declined`.

    **Ограничения:**
    - Доступен только владельцу регистрации
    - Регистрация должна быть в статусе `payment`

    **Параметры:**
    - `registration_id` - ID регистрации

    **Возвращает:** Обновленную регистрацию со статусом `declined`
    """
    logger.info(
        f"Payment decline attempt: registration_id={registration_id}, "
        f"user={user.telegram_username or user.telegram_id}"
    )

    # Получаем регистрацию
    registration = registration_crud.get_registration_by_id(db, registration_id)

    if not registration:
        logger.warning(
            f"Payment decline failed: Registration {registration_id} not found"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Registration not found"
        )

    # Проверяем, что регистрация принадлежит текущему пользователю
    if registration.user_id != user.id:
        logger.warning(
            f"Payment decline rejected: registration_id={registration_id} "
            f"belongs to user_id={registration.user_id}, not {user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. This registration belongs to another user.",
        )

    # Проверяем статус регистрации
    if registration.status != RegistrationStatusEnum.PAYMENT:
        logger.warning(
            f"Payment decline rejected: registration_id={registration_id}, "
            f"status={registration.status.value} (expected: payment)"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration is not in payment status. Current status: {registration.status.value}",
        )

    # Обновляем статус регистрации на declined
    registration.status = RegistrationStatusEnum.DECLINED
    db.commit()
    db.refresh(registration)

    logger.info(
        f"Payment decline successful: registration_id={registration_id}, "
        f"user={user.telegram_username or user.telegram_id}, "
        f"status changed to declined"
    )

    return registration
