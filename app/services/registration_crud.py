"""CRUD operations for Registration model."""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.user import User
from app.models.registration import Registration
from app.models.event import Event
from app.schemas.registration import RegistrationCreate, RegistrationStatusEnum


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


def get_event_registrations_with_users(
    db: Session,
    event_id: int,
    skip: int = 0,
    limit: int = 1000,
    status_filter: RegistrationStatusEnum | None = None,
    sort_by: str = "registered_at",
    sort_order: str = "asc",
) -> list[Registration]:
    """
    Получить все регистрации на мероприятие с данными пользователей.

    Использует joinedload для загрузки связанных пользователей.

    Args:
        db: Database session
        event_id: ID мероприятия
        skip: Количество записей для пропуска
        limit: Максимальное количество записей
        status_filter: Фильтр по статусу регистрации
        sort_by: Поле для сортировки ("registered_at" или "name")
        sort_order: Порядок сортировки ("asc" или "desc")
    """
    query = (
        db.query(Registration)
        .filter(Registration.event_id == event_id)
        .join(User)
        .options(joinedload(Registration.user))
    )

    # Применяем фильтр по статусу если указан
    if status_filter:
        query = query.filter(Registration.status == status_filter)

    # Применяем сортировку
    if sort_by == "name":
        # Сортировка по имени пользователя
        order_column = User.first_name
    else:
        # По умолчанию сортировка по времени регистрации
        order_column = Registration.registered_at

    if sort_order == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    return query.offset(skip).limit(limit).all()


def bulk_update_registration_statuses(
    db: Session, registration_ids: list[int], new_status: str
) -> int:
    """
    Массово обновить статусы регистраций.

    Args:
        db: Database session
        registration_ids: Список ID регистраций для обновления
        new_status: Новый статус

    Returns:
        int: Количество обновленных записей
    """

    # Конвертируем строку в enum если нужно
    if isinstance(new_status, str):
        new_status = RegistrationStatusEnum(new_status)

    updated_count = (
        db.query(Registration)
        .filter(Registration.id.in_(registration_ids))
        .update({"status": new_status}, synchronize_session=False)
    )
    db.commit()

    return updated_count
