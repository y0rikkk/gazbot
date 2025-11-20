"""Registration model."""

from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Registration(Base):
    """Модель регистрации на мероприятие."""

    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Дополнительная информация о регистрации
    comment = Column(Text, nullable=True)

    # Метаданные
    registered_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Registration(id={self.id}, user_id={self.user_id}, event_id={self.event_id})>"
