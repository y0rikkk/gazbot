"""Tests for main application endpoints."""

import pytest


def test_root_endpoint(client):
    """Тест корневого эндпоинта."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "GazBot API"
    assert data["status"] == "running"


def test_health_endpoint(client):
    """Тест health check эндпоинта."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
