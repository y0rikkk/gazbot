"""Tests for registrations API endpoints."""

import pytest
from datetime import datetime, timedelta

from app.models.user import User
from app.models.event import Event
from app.models.registration import Registration
from app.schemas.registration import RegistrationStatusEnum


def test_register_for_event_dev_mode(client, db_session, monkeypatch):
    """Тест регистрации на событие в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()
    future = now + timedelta(days=7)

    # Создаем пользователя и событие с датами в будущем
    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event = Event(
        title="Test Event",
        event_date=future,
        deadline=future,
        is_active=True,
    )

    db_session.add_all([user, event])
    db_session.commit()
    db_session.refresh(event)

    # Регистрируемся на событие
    response = client.post(
        f"/api/events/{event.id}/register",
        headers={"X-Telegram-Init-Data": "123"},
        json={
            "user_data": {
                "first_name": "Updated",
                "last_name": "User",
                "phone": "+1234567890",
                "isu": 123456,
            }
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["event_id"] == event.id
    assert data["user_id"] == user.id
    assert data["status"] == "pending"
    assert "check_in_token" in data


def test_get_user_registrations_dev_mode(client, db_session, monkeypatch):
    """Тест получения регистраций пользователя в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем пользователя, события и регистрации
    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event1 = Event(title="Event 1", event_date=now, deadline=now, is_active=True)
    event2 = Event(title="Event 2", event_date=now, deadline=now, is_active=False)

    db_session.add_all([user, event1, event2])
    db_session.commit()

    reg1 = Registration(
        user_id=user.id,
        event_id=event1.id,
        check_in_token="token1",
        status=RegistrationStatusEnum.PENDING,
    )
    reg2 = Registration(
        user_id=user.id,
        event_id=event2.id,
        check_in_token="token2",
        status=RegistrationStatusEnum.ACCEPTED,
    )

    db_session.add_all([reg1, reg2])
    db_session.commit()

    # Получаем текущую регистрацию пользователя (только для активного события)
    response = client.get(
        "/api/registrations/my",
        headers={"X-Telegram-Init-Data": "123"},
    )

    assert response.status_code == 200
    data = response.json()
    # Эндпоинт возвращает одну регистрацию (для активного события)
    assert isinstance(data, dict)
    assert data["user_id"] == user.id
    assert data["event_id"] == event1.id  # Активное событие


def test_get_registration_qr_code_dev_mode(client, db_session, monkeypatch):
    """Тест получения QR кода регистрации в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем пользователя, событие и регистрацию
    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.ACCEPTED,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Получаем QR код
    response = client.get(
        f"/api/registrations/{registration.id}/qr-code",
        headers={"X-Telegram-Init-Data": "123"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_registration_not_found(client, db_session, monkeypatch):
    """Тест получения несуществующей регистрации."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем пользователя
    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    db_session.add(user)
    db_session.commit()

    response = client.get(
        "/api/registrations/999/qr-code",
        headers={"X-Telegram-Init-Data": "123"},
    )

    assert response.status_code == 404
