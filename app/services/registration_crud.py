"""CRUD operations for Registration model."""

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.registration import Registration
from app.models.event import Event
from app.schemas.registration import RegistrationCreate


# def get_registration_by_id(db: Session, registration_id: int) -> Registration | None:
#     """Получить регистрацию по ID."""
#     return db.query(Registration).filter(Registration.id == registration_id).first()


def get_user_registration(
    db: Session, user_id: int, event_id: int
) -> Registration | None:
    """Проверить, зарегистрирован ли пользователь на мероприятие."""
    return (
        db.query(Registration)
        .filter(
            and_(Registration.user_id == user_id, Registration.event_id == event_id)
        )
        .first()
    )


def get_user_registrations(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> list[Registration]:
    """Получить все регистрации пользователя."""
    return (
        db.query(Registration)
        .filter(Registration.user_id == user_id)
        .order_by(Registration.registered_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# def get_event_registrations(
#     db: Session, event_id: int, skip: int = 0, limit: int = 100
# ) -> list[Registration]:
#     """Получить все регистрации на мероприятие."""
#     return (
#         db.query(Registration)
#         .filter(Registration.event_id == event_id)
#         .order_by(Registration.registered_at)
#         .offset(skip)
#         .limit(limit)
#         .all()
#     )


def create_registration(
    db: Session, user_id: int, registration: RegistrationCreate
) -> Registration:
    """Создать регистрацию на мероприятие."""
    db_registration = Registration(
        user_id=user_id,
        event_id=registration.event_id,
    )
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    return db_registration


# def delete_registration(db: Session, registration_id: int) -> bool:
#     """Удалить регистрацию."""
#     db_registration = get_registration_by_id(db, registration_id)
#     if not db_registration:
#         return False

#     db.delete(db_registration)
#     db.commit()
#     return True


# def count_event_registrations(db: Session, event_id: int) -> int:
#     """Подсчитать количество регистраций на мероприятие."""
#     return db.query(Registration).filter(Registration.event_id == event_id).count()
