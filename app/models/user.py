"""User model."""

from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean

from app.database import Base


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

    # Контактные данные
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Дополнительные данные профиля
    # (добавите свои поля когда будете создавать форму)
    bio = Column(String, nullable=True)

    # Метаданные
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
