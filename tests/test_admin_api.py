"""Тесты для админских API эндпоинтов."""

from datetime import datetime, timedelta
import pytest
from app.models import Event, User, Registration
from app.schemas import RegistrationStatusEnum


def test_get_all_events_unauthorized(client, db_session, monkeypatch):
    """Тест получения списка событий не-админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем обычного пользователя
    user = User(
        telegram_id=999,
        telegram_username="regular_user",
        first_name="Regular",
        last_name="User",
    )
    db_session.add(user)
    db_session.commit()

    # Запрос от обычного пользователя
    headers = {"X-Telegram-Init-Data": "999"}
    response = client.get("/api/admin/events", headers=headers)

    assert response.status_code == 403
    assert "admin" in response.json()["detail"].lower()


def test_get_all_events_as_admin(client, db_session, admin_user, monkeypatch):
    """Тест получения списка всех событий админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем события
    event1 = Event(
        title="Event 1",
        description="Description 1",
        event_date=datetime.now() + timedelta(days=7),
        deadline=datetime.now() + timedelta(days=5),
        location="Location 1",
        is_active=True,
    )
    event2 = Event(
        title="Event 2",
        description="Description 2",
        event_date=datetime.now() + timedelta(days=14),
        deadline=datetime.now() + timedelta(days=10),
        location="Location 2",
        is_active=False,
    )
    db_session.add_all([event1, event2])
    db_session.commit()

    # Запрос от админа (в DEV_MODE просто передаем telegram_id)
    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.get("/api/admin/events", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_create_event_as_admin(client, db_session, admin_user, monkeypatch):
    """Тест создания события админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    event_data = {
        "title": "New Event",
        "description": "New Description",
        "event_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "deadline": (datetime.now() + timedelta(days=5)).isoformat(),
        "location": "Test Location",
        "is_active": True,
    }

    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.post("/api/admin/events", json=event_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Event"
    assert data["location"] == "Test Location"
    assert data["is_active"] is True


def test_update_event_as_admin(client, db_session, admin_user, monkeypatch):
    """Тест обновления события админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем событие
    event = Event(
        title="Original Event",
        description="Original Description",
        event_date=datetime.now() + timedelta(days=7),
        deadline=datetime.now() + timedelta(days=5),
        location="Original Location",
        is_active=True,
    )
    db_session.add(event)
    db_session.commit()
    event_id = event.id

    # Обновляем событие
    update_data = {"title": "Updated Event", "location": "Updated Location"}

    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.put(
        f"/api/admin/events/{event_id}", json=update_data, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Event"
    assert data["location"] == "Updated Location"


def test_delete_event_as_admin(client, db_session, admin_user, monkeypatch):
    """Тест удаления события админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем событие
    event = Event(
        title="Event to Delete",
        description="Will be deleted",
        event_date=datetime.now() + timedelta(days=7),
        deadline=datetime.now() + timedelta(days=5),
        location="Some Location",
        is_active=False,
    )
    db_session.add(event)
    db_session.commit()
    event_id = event.id

    # Удаляем событие
    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.delete(f"/api/admin/events/{event_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_get_event_registrations_as_admin(client, db_session, admin_user, monkeypatch):
    """Тест получения регистраций на событие админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем пользователя и событие
    user = User(
        telegram_id=123,
        telegram_username="testuser",
        first_name="Test",
        last_name="User",
    )
    event = Event(
        title="Test Event",
        description="Description",
        event_date=datetime.now() + timedelta(days=7),
        deadline=datetime.now() + timedelta(days=5),
        location="Test Location",
        is_active=True,
    )
    db_session.add_all([user, event])
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

    # Запрос от админа
    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.get(
        f"/api/admin/events/{event.id}/registrations", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "pending"


def test_bulk_update_registrations_as_admin(
    client, db_session, admin_user, monkeypatch
):
    """Тест массового обновления статусов регистраций админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем пользователей и событие
    user1 = User(
        telegram_id=111, telegram_username="user1", first_name="User", last_name="One"
    )
    user2 = User(
        telegram_id=222, telegram_username="user2", first_name="User", last_name="Two"
    )
    event = Event(
        title="Test Event",
        description="Description",
        event_date=datetime.now() + timedelta(days=7),
        deadline=datetime.now() + timedelta(days=5),
        location="Test Location",
        is_active=True,
    )
    db_session.add_all([user1, user2, event])
    db_session.commit()

    # Создаем регистрации
    reg1 = Registration(
        user_id=user1.id,
        event_id=event.id,
        status=RegistrationStatusEnum.PENDING,
        check_in_token="token1",
    )
    reg2 = Registration(
        user_id=user2.id,
        event_id=event.id,
        status=RegistrationStatusEnum.PENDING,
        check_in_token="token2",
    )
    db_session.add_all([reg1, reg2])
    db_session.commit()

    # Массово одобряем регистрации
    update_data = {"registration_ids": [reg1.id, reg2.id], "status": "accepted"}

    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.post(
        "/api/admin/registrations/bulk_update_statuses",
        json=update_data,
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_check_in_user_as_admin(client, db_session, admin_user, monkeypatch):
    """Тест регистрации прихода пользователя админом."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем пользователя и событие
    user = User(
        telegram_id=123,
        telegram_username="testuser",
        first_name="Test",
        last_name="User",
    )
    event = Event(
        title="Test Event",
        description="Description",
        event_date=datetime.now() + timedelta(days=7),
        deadline=datetime.now() + timedelta(days=5),
        location="Test Location",
        is_active=True,
    )
    db_session.add_all([user, event])
    db_session.commit()

    # Создаем одобренную регистрацию
    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        status=RegistrationStatusEnum.ACCEPTED,
        check_in_token="test_token_123",
    )
    db_session.add(registration)
    db_session.commit()

    # Отмечаем приход
    check_in_data = {"token": "test_token_123"}
    headers = {"X-Telegram-Init-Data": str(admin_user["id"])}
    response = client.post("/api/admin/check-in", json=check_in_data, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["telegram_id"] == 123
    assert data["checked_in_at"] is not None


def test_admin_endpoint_without_auth(client):
    """Тест доступа к админским эндпоинтам без авторизации."""
    response = client.get("/api/admin/events")
    # 422 - отсутствует обязательный заголовок X-Telegram-Init-Data
    assert response.status_code == 422
