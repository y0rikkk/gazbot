"""Tests for events API endpoints."""

import pytest
from datetime import datetime, timedelta

from app.models.event import Event


def test_get_current_event(client, db_session):
    """Тест получения активного события."""
    now = datetime.now()
    future = now + timedelta(days=7)

    # Создаем активное событие с датой в будущем
    active_event = Event(
        title="Active Event",
        description="Active description",
        event_date=future,
        deadline=future,
        is_active=True,
    )

    db_session.add(active_event)
    db_session.commit()
    db_session.refresh(active_event)

    response = client.get("/api/events/current")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == active_event.id
    assert data["title"] == "Active Event"
    assert data["is_active"] is True


def test_get_current_event_not_found(client, db_session):
    """Тест получения активного события когда его нет."""
    response = client.get("/api/events/current")

    assert response.status_code == 404
    assert "active event" in response.json()["detail"].lower()
