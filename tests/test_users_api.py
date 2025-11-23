"""Tests for users API endpoints."""

import pytest

from app.models.user import User


def test_get_current_user_dev_mode(client, db_session, monkeypatch):
    """Тест получения текущего пользователя в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем пользователя
    user = User(
        telegram_id=123,
        telegram_username="testuser",
        first_name="Test",
        last_name="User",
        phone="+1234567890",
        isu=123456,
        address="Test Address",
    )

    db_session.add(user)
    db_session.commit()

    # Получаем текущего пользователя
    response = client.get(
        "/api/users/me",
        headers={"X-Telegram-Init-Data": "123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["telegram_id"] == 123
    assert data["telegram_username"] == "testuser"
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"
    assert data["phone"] == "+1234567890"
    assert data["isu"] == 123456
    assert data["address"] == "Test Address"


def test_update_current_user_dev_mode(client, db_session, monkeypatch):
    """Тест обновления данных текущего пользователя в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    # Создаем пользователя
    user = User(
        telegram_id=123,
        telegram_username="testuser",
        first_name="Test",
    )

    db_session.add(user)
    db_session.commit()

    # Обновляем данные пользователя
    response = client.put(
        "/api/users/me",
        headers={"X-Telegram-Init-Data": "123"},
        json={
            "first_name": "Updated",
            "last_name": "Name",
            "phone": "+9876543210",
            "isu": 654321,
            "address": "New Address",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"
    assert data["phone"] == "+9876543210"
    assert data["isu"] == 654321
    assert data["address"] == "New Address"


def test_get_user_unauthorized(client, db_session):
    """Тест получения пользователя без аутентификации."""
    response = client.get("/api/users/me")

    assert response.status_code == 422  # Missing required header


def test_get_user_not_found_dev_mode(client, db_session, monkeypatch):
    """Тест получения несуществующего пользователя в DEV_MODE."""
    monkeypatch.setenv("DEV_MODE", "true")

    response = client.get(
        "/api/users/me",
        headers={"X-Telegram-Init-Data": "999"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
