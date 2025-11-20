"""
Примеры использования Pydantic схем
"""

# Пример использования User схем
from datetime import datetime
from app.schemas.user import UserCreate, UserUpdate, User

# Создание пользователя
user_create_data = {
    "telegram_id": 123456789,
    "telegram_username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+79001234567",
    "isu": 312345,
}
user_create = UserCreate(**user_create_data)

# Обновление пользователя
user_update_data = {"phone": "+79009876543", "isu": 312346}
user_update = UserUpdate(**user_update_data)

# Пример пользователя из БД
user_data = {
    "id": 1,
    "telegram_id": 123456789,
    "telegram_username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+79001234567",
    "isu": 312345,
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
}
user = User(**user_data)


# Пример использования Event схем
from app.schemas.event import EventCreate, Event, EventWithRegistrationCount

event_create_data = {
    "title": "Новогодняя вечеринка 2025",
    "description": "Праздничное мероприятие с музыкой и развлечениями",
    "event_date": datetime(2025, 12, 31, 20, 0),
    "location": "ул. Ломоносова, 9",
    "deadline": datetime(2025, 12, 25, 23, 59),
}
event_create = EventCreate(**event_create_data)

# Event с количеством регистраций
event_with_count_data = {
    **event_create_data,
    "id": 1,
    "created_at": datetime.now(),
    "updated_at": datetime.now(),
    "registrations_count": 15,
}
event_with_count = EventWithRegistrationCount(**event_with_count_data)


# Пример использования Registration схем
from app.schemas.registration import RegistrationCreate, RegistrationWithDetails

registration_create_data = {"event_id": 1}
registration_create = RegistrationCreate(**registration_create_data)

# Registration с деталями
registration_with_details_data = {
    "id": 1,
    "user_id": 1,
    "event_id": 1,
    "registered_at": datetime.now(),
    "user": user_data,
    "event": event_create_data
    | {"id": 1, "created_at": datetime.now(), "updated_at": datetime.now()},
}
# registration_with_details = RegistrationWithDetails(**registration_with_details_data)


# Пример использования Telegram схем
from app.schemas.telegram import TelegramUser, MessageSend

telegram_user_data = {
    "id": 123456789,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "language_code": "ru",
    "is_premium": False,
}
telegram_user = TelegramUser(**telegram_user_data)

message_send_data = {
    "telegram_id": 123456789,
    "message": "Привет! Вы успешно зарегистрированы на мероприятие.",
}
message_send = MessageSend(**message_send_data)


# Пример использования Common схем
from app.schemas.common import ResponseBase, ErrorResponse, PaginatedResponse

# Успешный ответ с данными
response_success = ResponseBase(
    success=True, message="User retrieved successfully", data=user.model_dump()
)

# Ответ с ошибкой
response_error = ErrorResponse(
    success=False,
    message="User not found",
    detail="User with telegram_id 123456789 does not exist",
)

# Ответ с пагинацией
response_paginated = PaginatedResponse(
    success=True, total=50, skip=0, limit=10, data=[event_with_count.model_dump()]
)

print("✓ All schema examples created successfully!")
