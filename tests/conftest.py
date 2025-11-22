"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Тестовая база данных (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Создание тестовой сессии БД."""
    # Создаем таблицы
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Удаляем таблицы после теста
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Создание тестового клиента FastAPI."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session, monkeypatch):
    """Fixture для создания админского пользователя.

    Устанавливает ADMIN_IDS в переменные окружения и создает пользователя в БД.
    """
    from app.models import User
    from app.core.config import settings

    admin_id = 123456789

    # Патчим переменную окружения
    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", str(admin_id))

    # Патчим саму проперти admin_ids_list в settings
    monkeypatch.setattr(
        type(settings), "admin_ids_list", property(lambda self: [admin_id])
    )

    # Создаем пользователя в БД
    admin = User(
        telegram_id=admin_id,
        telegram_username="admin_user",
        first_name="Admin",
        last_name="User",
    )
    db_session.add(admin)
    db_session.commit()

    return {
        "id": admin_id,
        "first_name": "Admin",
        "last_name": "User",
        "username": "admin_user",
    }
