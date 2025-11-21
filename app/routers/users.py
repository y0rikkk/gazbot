"""User routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import User, UserUpdate
from app.schemas.event import Event
from app.schemas.common import ResponseBase
from app.services import user_crud, registration_crud, event_crud
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
    events = event_crud.get_user_events(db, user.id, skip, limit)

    return events
