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


def test_upload_payment_receipt_dev_mode(client, db_session, monkeypatch):
    """Тест загрузки квитанции об оплате в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем пользователя, событие и регистрацию в статусе payment
    user = User(
        telegram_id=123,
        telegram_username="testuser",
        first_name="Test",
        last_name="User",
    )
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.PAYMENT,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Создаем тестовый файл (PNG)
    test_file_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

    # Загружаем квитанцию
    response = client.post(
        f"/api/registrations/{registration.id}/payment",
        headers={"X-Telegram-Init-Data": "123"},
        files={"receipt": ("receipt.png", test_file_content, "image/png")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    # Проверяем, что статус изменился на accepted
    db_session.refresh(registration)
    assert registration.status == RegistrationStatusEnum.ACCEPTED


def test_upload_payment_wrong_status(client, db_session, monkeypatch):
    """Тест загрузки квитанции когда регистрация не в статусе payment."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем регистрацию в статусе pending
    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.PENDING,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    test_file_content = b"\x89PNG\r\n\x1a\n"

    response = client.post(
        f"/api/registrations/{registration.id}/payment",
        headers={"X-Telegram-Init-Data": "123"},
        files={"receipt": ("receipt.png", test_file_content, "image/png")},
    )

    assert response.status_code == 400
    assert "not in payment status" in response.json()["detail"]


def test_upload_payment_invalid_format(client, db_session, monkeypatch):
    """Тест загрузки квитанции с недопустимым форматом."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.PAYMENT,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Загружаем файл с недопустимым расширением
    response = client.post(
        f"/api/registrations/{registration.id}/payment",
        headers={"X-Telegram-Init-Data": "123"},
        files={"receipt": ("receipt.txt", b"test", "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_upload_payment_file_too_large(client, db_session, monkeypatch):
    """Тест загрузки слишком большого файла."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.PAYMENT,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Создаем файл больше 10 MB
    large_file = b"x" * (11 * 1024 * 1024)

    response = client.post(
        f"/api/registrations/{registration.id}/payment",
        headers={"X-Telegram-Init-Data": "123"},
        files={"receipt": ("receipt.png", large_file, "image/png")},
    )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]


def test_decline_payment_dev_mode(client, db_session, monkeypatch):
    """Тест отклонения оплаты в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем пользователя, событие и регистрацию в статусе payment
    user = User(telegram_id=123, telegram_username="testuser", first_name="Test")
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user, event])
    db_session.commit()

    registration = Registration(
        user_id=user.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.PAYMENT,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Отклоняем оплату
    response = client.post(
        f"/api/registrations/{registration.id}/decline",
        headers={"X-Telegram-Init-Data": "123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == registration.id
    assert data["status"] == "declined"

    # Проверяем, что статус в БД изменился
    db_session.refresh(registration)
    assert registration.status == RegistrationStatusEnum.DECLINED


def test_decline_payment_wrong_status(client, db_session, monkeypatch):
    """Тест отклонения оплаты когда регистрация не в статусе payment."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем регистрацию в статусе accepted
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

    response = client.post(
        f"/api/registrations/{registration.id}/decline",
        headers={"X-Telegram-Init-Data": "123"},
    )

    assert response.status_code == 400
    assert "not in payment status" in response.json()["detail"]


def test_decline_payment_not_owner(client, db_session, monkeypatch):
    """Тест отклонения оплаты другого пользователя."""
    monkeypatch.setenv("DEV_MODE", "true")

    now = datetime.now()

    # Создаем двух пользователей
    user1 = User(telegram_id=123, telegram_username="testuser1", first_name="Test1")
    user2 = User(telegram_id=456, telegram_username="testuser2", first_name="Test2")
    event = Event(title="Test Event", event_date=now, deadline=now, is_active=True)

    db_session.add_all([user1, user2, event])
    db_session.commit()

    # Регистрация принадлежит user1
    registration = Registration(
        user_id=user1.id,
        event_id=event.id,
        check_in_token="test_token_123",
        status=RegistrationStatusEnum.PAYMENT,
    )

    db_session.add(registration)
    db_session.commit()
    db_session.refresh(registration)

    # Пытаемся отклонить от имени user2
    response = client.post(
        f"/api/registrations/{registration.id}/decline",
        headers={"X-Telegram-Init-Data": "456"},
    )

    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]
