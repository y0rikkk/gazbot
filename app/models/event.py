"""Event model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

from app.database import Base


class Event(Base):
    """Модель мероприятия."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Дата и время события
    event_date = Column(DateTime, nullable=False)

    # Местоположение
    location = Column(String, nullable=True)

    # Ограничения
    max_participants = Column(Integer, nullable=True)

    # Статус
    is_active = Column(Boolean, default=True)
    is_published = Column(Boolean, default=False)

    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return (
            f"<Event(id={self.id}, title={self.title}, event_date={self.event_date})>"
        )
