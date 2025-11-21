"""Registration model."""

from datetime import datetime
from app.schemas.registration import RegistrationStatusEnum

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, Text, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class Registration(Base):
    """Модель регистрации на мероприятие."""

    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # Relationships
    user = relationship("User", backref="registrations")
    event = relationship("Event", backref="registrations")

    # Статус регистрации
    status = Column(
        Enum(RegistrationStatusEnum),
        nullable=False,
        default=RegistrationStatusEnum.PENDING,
    )

    # Метаданные
    registered_at = Column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"<Registration(id={self.id}, user_id={self.user_id}, event_id={self.event_id})>"
