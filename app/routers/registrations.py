"""Registrations routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.registration import Registration
from app.services import event_crud, registration_crud
from app.core.auth import CurrentUser
from app.core.qr_code import generate_qr_code_image


router = APIRouter()


@router.get("/my", response_model=Registration)
def get_user_current_registration(user: CurrentUser, db: Session = Depends(get_db)):
    """
    Получить активную регистрацию.

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


@router.get("/{registration_id}/qr-code")
def get_registration_qr_code(
    registration_id: int,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Получить QR-код для регистрации (билет на мероприятие).

    QR-код содержит уникальный токен, который можно отсканировать
    для отметки прихода на мероприятие.

    Параметры:
    - registration_id: ID регистрации
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
