"""CRUD operations for Event model."""

from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.registration import Registration
from app.schemas.event import EventCreate, EventUpdate


def get_event_by_id(db: Session, event_id: int) -> Event | None:
    """Получить мероприятие по ID."""
    return db.query(Event).filter(Event.id == event_id).first()


def get_user_events(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Event)
        .join(Registration)
        .filter(Registration.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_active_event(db: Session) -> Event | None:
    """Получить активное мероприятие."""
    return (
        db.query(Event)
        .filter(Event.is_active == True)
        .order_by(Event.event_date.desc())
        .first()
    )


def get_all_events(db: Session, skip: int = 0, limit: int = 100) -> list[Event]:
    """Получить список всех мероприятий."""
    return (
        db.query(Event)
        .order_by(Event.event_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_event(db: Session, event: EventCreate) -> Event:
    """
    Создать новое мероприятие.

    Raises:
        IntegrityError: Если пытаемся создать второе активное мероприятие
    """
    db_event = Event(
        title=event.title,
        description=event.description,
        event_date=event.event_date,
        location=event.location,
        deadline=event.deadline,
        is_active=event.is_active,
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


def update_event(db: Session, event_id: int, event_update: EventUpdate) -> Event | None:
    """
    Обновить мероприятие.

    Raises:
        IntegrityError: Если пытаемся сделать активным второе мероприятие
    """
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return None

    update_data = event_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


def delete_event(db: Session, event_id: int) -> bool:
    """Удалить мероприятие."""
    db_event = get_event_by_id(db, event_id)
    if not db_event:
        return False

    db.delete(db_event)
    db.commit()
    return True
