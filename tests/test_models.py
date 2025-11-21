"""Tests for database models."""

import pytest
from datetime import datetime

from app.models.user import User
from app.models.event import Event
from app.models.registration import Registration
from app.schemas.registration import RegistrationStatusEnum


def test_create_user(db_session):
    """Тест создания пользователя."""
    user = User(
        telegram_id=12345,
        telegram_username="testuser",
        first_name="Test",
        last_name="User",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.telegram_id == 12345
    assert user.telegram_username == "testuser"
    assert user.created_at is not None


def test_create_event(db_session):
    """Тест создания события."""
    now = datetime.now()
    event = Event(
        title="Test Event",
        description="Test description",
        location="Test location",
        event_date=now,
        deadline=now,
        is_active=True,
    )

    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.title == "Test Event"
    assert event.is_active is True
    assert event.created_at is not None


def test_create_registration(db_session):
    """Тест создания регистрации."""
    # Создаем пользователя и событие
    now = datetime.now()
    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now)

    db_session.add(user)
    db_session.add(event)
    db_session.commit()

    # Создаем регистрацию
    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        status=RegistrationStatusEnum.PENDING,
        check_in_token="test_token_123",
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    assert registration.id is not None
    assert registration.user_id == user.id
    assert registration.event_id == event.id
    assert registration.status == RegistrationStatusEnum.PENDING
    assert registration.registered_at is not None


def test_user_registrations_relationship(db_session):
    """Тест связи пользователь-регистрации."""
    now = datetime.now()
    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")

    # Создаем первое событие (активное)
    event1 = Event(title="Event 1", event_date=now, deadline=now, is_active=True)

    db_session.add(user)
    db_session.add(event1)
    db_session.commit()

    # Создаем второе событие (неактивное) - SQLite не позволяет два is_active=False
    event2 = Event(title="Event 2", event_date=now, deadline=now, is_active=False)
    db_session.add(event2)
    db_session.commit()

    # Создаем две регистрации
    reg1 = Registration(user_id=user.id, event_id=event1.id, check_in_token="token1")
    reg2 = Registration(user_id=user.id, event_id=event2.id, check_in_token="token2")

    db_session.add_all([reg1, reg2])
    db_session.commit()

    # Проверяем связь
    db_session.refresh(user)
    assert len(user.registrations) == 2
