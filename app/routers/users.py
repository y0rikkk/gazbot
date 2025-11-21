"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import User, UserUpdate
from app.schemas.registration import Registration
from app.schemas.event import Event
from app.schemas.common import ResponseBase
from app.services import user_crud, registration_crud
from app.models import event as event_model
from app.core.auth import CurrentUser

router = APIRouter()


@router.get("/me", response_model=User)
def get_current_user_profile(user: CurrentUser):
    """
    Получить профиль текущего пользователя.

    Автоматически определяет пользователя из Telegram Web App initData.
    """
    return user


# @router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
# def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
#     """
#     Зарегистрировать нового пользователя или получить существующего.

#     Параметры:
#     - user_data: Данные для регистрации пользователя
#     """
#     # Проверяем, существует ли пользователь
#     existing_user = user_crud.get_user_by_telegram_id(db, user_data.telegram_id)
#     if existing_user:
#         # Если пользователь существует, обновляем его данные
#         update_data = UserUpdate(
#             first_name=user_data.first_name,
#             last_name=user_data.last_name,
#             phone=user_data.phone,
#             isu=user_data.isu,
#         )
#         updated_user = user_crud.update_user(db, existing_user.id, update_data)
#         return updated_user

#     # Создаем нового пользователя
#     return user_crud.create_user(db, user_data)


@router.put("/me", response_model=User)
def update_current_user_profile(
    user_update: UserUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    """
    Обновить профиль текущего пользователя.
    """
    updated_user = user_crud.update_user(db, user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )
    return updated_user


# @router.get("/me/registrations", response_model=list[Registration])
# def get_my_registrations(
#     telegram_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
# ):
#     """
#     Получить список регистраций текущего пользователя.

#     Параметры:
#     - telegram_id: ID пользователя в Telegram
#     - skip: Количество записей для пропуска
#     - limit: Максимальное количество записей
#     """
#     user = user_crud.get_user_by_telegram_id(db, telegram_id)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
#         )

#     registrations = registration_crud.get_user_registrations(db, user.id, skip, limit)
#     return registrations


@router.get("/me/events", response_model=list[Event])
def get_my_events(
    user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Получить список мероприятий, на которых был пользователь.
    """
    registrations = registration_crud.get_user_registrations(db, user.id, skip, limit)

    # Получаем события для каждой регистрации
    events = []
    for reg in registrations:
        event = (
            db.query(event_model.Event)
            .filter(event_model.Event.id == reg.event_id)
            .first()
        )
        if event:
            events.append(event)

    return events


@router.get("/greeting")
def get_greeting(user: CurrentUser):
    """
    Получить приветствие для главной страницы.
    """
    name = user.first_name if user.first_name else "Гость"

    return ResponseBase(success=True, message=f"Привет, {name}!", data={"name": name})
