# GazBot API

Backend для Telegram Web App регистрации на тематические вечеринки.

## Технологии

- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM (синхронный режим)
- **PostgreSQL** - база данных
- **Alembic** - миграции БД
- **python-telegram-bot** - интеграция с Telegram Bot API
- **Poetry** - управление зависимостями

## Структура проекта

```
gazbot/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── database.py          # Настройка БД и сессий
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Настройки приложения
│   ├── models/              # SQLAlchemy модели
│   │   └── __init__.py
│   ├── schemas/             # Pydantic схемы
│   │   └── __init__.py
│   ├── routers/             # API endpoints
│   │   └── __init__.py
│   └── services/            # Бизнес-логика
│       └── __init__.py
├── alembic/                 # Миграции БД (будет создано)
├── .env                     # Переменные окружения (создать из .env.example)
├── .env.example             # Пример конфигурации
├── .gitignore
└── pyproject.toml           # Poetry dependencies
```

## Установка и запуск

### 1. Клонируйте репозиторий и установите зависимости

```bash
poetry install
```

### 2. Настройте PostgreSQL

Создайте базу данных:

```bash
createdb gazbot
# или через psql:
# CREATE DATABASE gazbot;
```

### 3. Настройте переменные окружения

Скопируйте `.env.example` в `.env` и заполните необходимые переменные:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

- `DATABASE_URL` - строка подключения к PostgreSQL (уже настроено для локальной БД)
- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота (получите у @BotFather)
- `TELEGRAM_BOT_USERNAME` - username вашего бота
- `ADMIN_TELEGRAM_IDS` - список telegram_id администраторов через запятую

### 4. Примените миграции

```bash
poetry run alembic upgrade head
```

### 5. Запустите приложение

```bash
poetry run uvicorn app.main:app --reload
```

API будет доступен по адресу: http://localhost:8000

Документация: http://localhost:8000/docs

## База данных

### Модели

- **User** - пользователи (telegram_id, имя, контакты, профиль)
- **Event** - мероприятия (название, дата, описание, локация)
- **Registration** - регистрации на мероприятия (связь user-event)

### Миграции

Подробные команды для работы с миграциями смотрите в `COMMANDS.md`.

## Следующие шаги

1. ✅ Создать модели БД (`app/models/`)
2. ✅ Настроить Alembic и создать миграции
3. Создать Pydantic схемы (`app/schemas/`)
4. Реализовать API endpoints (`app/routers/`)
5. Добавить сервисы для работы с Telegram Bot (`app/services/`)
6. Добавить middleware для валидации Telegram Web App initData
