"""CRUD operations for User model."""

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_telegram_id(db: Session, telegram_id: int) -> User | None:
    """Получить пользователя по telegram_id."""
    return db.query(User).filter(User.telegram_id == telegram_id).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Получить пользователя по ID."""
    return db.query(User).filter(User.id == user_id).first()


# def create_user(db: Session, user: UserCreate) -> User:
#     """Создать нового пользователя."""
#     db_user = User(
#         telegram_id=user.telegram_id,
#         telegram_username=user.telegram_username,
#         first_name=user.first_name,
#         last_name=user.last_name,
#         phone=user.phone,
#         isu=user.isu,
#     )
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User | None:
    """Обновить данные пользователя."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    # Обновляем только те поля, которые были переданы
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if getattr(db_user, field) != value:
            setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


# def get_or_create_user(db: Session, user: UserCreate) -> tuple[User, bool]:
#     """
#     Получить существующего или создать нового пользователя.

#     Returns:
#         tuple[User, bool]: (пользователь, был_ли_создан)
#     """
#     db_user = get_user_by_telegram_id(db, user.telegram_id)
#     if db_user:
#         return db_user, False

#     return create_user(db, user), True
