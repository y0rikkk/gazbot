"""Tests for CRUD services."""

import pytest
from datetime import datetime, timedelta

from app.models.user import User
from app.models.event import Event
from app.models.registration import Registration
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.event import EventCreate, EventUpdate
from app.schemas.registration import RegistrationCreate, RegistrationStatusEnum
from app.services import user_crud, event_crud, registration_crud


# User CRUD tests
def test_create_user_service(db_session):
    """Тест создания пользователя через сервис."""
    user_data = UserCreate(
        telegram_id=12345,
        telegram_username="testuser",
        first_name="Test",
        last_name="User",
        phone="+1234567890",
        isu=123456,
        address="Test Address",
    )

    user = user_crud.create_user(db_session, user_data)

    assert user.id is not None
    assert user.telegram_id == 12345
    assert user.telegram_username == "testuser"
    assert user.first_name == "Test"
    assert user.last_name == "User"


def test_get_user_by_telegram_id(db_session):
    """Тест получения пользователя по telegram_id."""
    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    db_session.add(user)
    db_session.commit()

    found_user = user_crud.get_user_by_telegram_id(db_session, 12345)

    assert found_user is not None
    assert found_user.telegram_id == 12345


def test_update_user_service(db_session):
    """Тест обновления пользователя через сервис."""
    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    db_session.add(user)
    db_session.commit()

    update_data = UserUpdate(
        first_name="Updated",
        last_name="Name",
        phone="+9876543210",
    )

    updated_user = user_crud.update_user(db_session, user.id, update_data)

    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"
    assert updated_user.phone == "+9876543210"


# Event CRUD tests
def test_create_event_service(db_session):
    """Тест создания события через сервис."""
    now = datetime.now()
    future = now + timedelta(days=7)

    event_data = EventCreate(
        title="Test Event",
        description="Test description",
        event_date=future,
        location="Test location",
        deadline=future,
        is_active=True,
    )

    event = event_crud.create_event(db_session, event_data)

    assert event.id is not None
    assert event.title == "Test Event"
    assert event.is_active is True


def test_get_event_by_id_service(db_session):
    """Тест получения события по ID через сервис."""
    now = datetime.now()
    event = Event(title="Test Event", event_date=now, deadline=now)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    found_event = event_crud.get_event_by_id(db_session, event.id)

    assert found_event is not None
    assert found_event.id == event.id


def test_get_active_event_service(db_session):
    """Тест получения активного события через сервис."""
    now = datetime.now()
    future = now + timedelta(days=7)

    active_event = Event(
        title="Active Event",
        event_date=future,
        deadline=future,
        is_active=True,
    )
    inactive_event = Event(
        title="Inactive Event",
        event_date=future,
        deadline=future,
        is_active=False,
    )

    db_session.add(active_event)
    db_session.commit()
    db_session.add(inactive_event)
    db_session.commit()

    found_event = event_crud.get_active_event(db_session)

    assert found_event is not None
    assert found_event.title == "Active Event"
    assert found_event.is_active is True


def test_update_event_service(db_session):
    """Тест обновления события через сервис."""
    now = datetime.now()
    event = Event(title="Test Event", event_date=now, deadline=now)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    update_data = EventUpdate(
        title="Updated Event",
        description="Updated description",
    )

    updated_event = event_crud.update_event(db_session, event.id, update_data)

    assert updated_event.title == "Updated Event"
    assert updated_event.description == "Updated description"


def test_delete_event_service(db_session):
    """Тест удаления события через сервис."""
    now = datetime.now()
    event = Event(title="Test Event", event_date=now, deadline=now)
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    result = event_crud.delete_event(db_session, event.id)

    assert result is True

    # Проверяем что событие удалено
    deleted_event = event_crud.get_event_by_id(db_session, event.id)
    assert deleted_event is None


# Registration CRUD tests
def test_create_registration_service(db_session):
    """Тест создания регистрации через сервис."""
    now = datetime.now()

    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now)

    db_session.add_all([user, event])
    db_session.commit()

    reg_data = RegistrationCreate(event_id=event.id)
    registration = registration_crud.create_registration(db_session, user.id, reg_data)

    assert registration.id is not None
    assert registration.user_id == user.id
    assert registration.event_id == event.id
    assert registration.check_in_token is not None


def test_get_user_registration(db_session):
    """Тест получения регистрации пользователя на событие."""
    now = datetime.now()

    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token",
    )

    db_session.add(registration)
    db_session.commit()

    found_reg = registration_crud.get_user_registration(db_session, user.id, event.id)

    assert found_reg is not None
    assert found_reg.user_id == user.id
    assert found_reg.event_id == event.id


def test_bulk_update_registration_statuses(db_session):
    """Тест массового обновления статусов регистраций."""
    now = datetime.now()

    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token",
        status=RegistrationStatusEnum.PENDING,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Массово обновляем статус
    count = registration_crud.bulk_update_registration_statuses(
        db_session,
        [registration.id],
        RegistrationStatusEnum.ACCEPTED,
    )

    assert count == 1
    db_session.refresh(registration)
    assert registration.status == RegistrationStatusEnum.ACCEPTED


def test_get_registration_by_token(db_session):
    """Тест получения регистрации по токену."""
    now = datetime.now()

    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="unique_token_123",
        status=RegistrationStatusEnum.ACCEPTED,
    )

    db_session.add(registration)
    db_session.commit()

    # Получаем регистрацию по токену
    found_reg = registration_crud.get_registration_by_token(
        db_session,
        "unique_token_123",
    )

    assert found_reg is not None
    assert found_reg.check_in_token == "unique_token_123"
    assert found_reg.user_id == user.id


def test_mark_checked_in(db_session):
    """Тест отметки check-in."""
    now = datetime.now()

    user = User(telegram_id=12345, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token",
        status=RegistrationStatusEnum.ACCEPTED,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Отмечаем check-in
    checked_in_reg = registration_crud.mark_checked_in(db_session, registration.id)

    assert checked_in_reg is not None
    assert checked_in_reg.checked_in_at is not None
