# GazBot - Инструкция по развертыванию с Docker

## Быстрый старт

### 1. Подготовка

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и заполните необходимые переменные:

- `TELEGRAM_BOT_TOKEN` - токен вашего бота
- `TELEGRAM_WEBHOOK_URL` - URL вебхука (если используете)
- `ADMIN_TELEGRAM_IDS` - ID администраторов через запятую

### 2. Запуск

Запустите приложение с помощью Docker Compose:

```bash
docker-compose up -d
```

Это запустит:

- PostgreSQL базу данных на порту 5432
- FastAPI приложение на порту 8000

### 3. Проверка

Проверьте, что сервисы запущены:

```bash
docker-compose ps
```

Проверьте логи:

```bash
docker-compose logs -f app
```

Откройте в браузере:

- API документация: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 4. Применение миграций

Выполните миграции базы данных:

```bash
docker-compose exec app alembic upgrade head
```

### 5. Остановка

Остановить сервисы:

```bash
docker-compose down
```

Остановить и удалить volumes (БД будет очищена):

```bash
docker-compose down -v
```

## Структура

```
gazbot/
├── docker-compose.yml   # Конфигурация Docker Compose
├── Dockerfile          # Образ приложения
├── .dockerignore       # Исключения для Docker build
├── .env               # Переменные окружения (создайте из .env.example)
└── .env.example       # Пример переменных окружения
```

## Переменные окружения

### Обязательные:

- `TELEGRAM_BOT_TOKEN` - токен Telegram бота
- `ADMIN_TELEGRAM_IDS` - ID администраторов

### Опциональные:

- `DATABASE_URL` - строка подключения к БД (по умолчанию используется PostgreSQL из docker-compose)
- `DEBUG` - режим отладки (true/false)
- `DEV_MODE` - режим разработки (true/false)
- `LOG_LEVEL` - уровень логирования (DEBUG/INFO/WARNING/ERROR)
- `TELEGRAM_WEBHOOK_URL` - URL для вебхука

## Логи

Логи приложения сохраняются в директории `logs/` и доступны как внутри контейнера, так и на хосте.

```bash
# Просмотр логов приложения
docker-compose logs -f app

# Просмотр логов БД
docker-compose logs -f postgres

# Просмотр файлов логов
tail -f logs/app.log
```

## Backup базы данных

Создать backup:

```bash
docker-compose exec postgres pg_dump -U gazbot gazbot_db > backup.sql
```

Восстановить из backup:

```bash
docker-compose exec -T postgres psql -U gazbot gazbot_db < backup.sql
```

## Разработка

Для разработки с hot-reload:

1. Закомментируйте в `docker-compose.yml` строку `restart: unless-stopped`
2. Добавьте volume для кода:
   ```yaml
   volumes:
     - .:/app
     - ./logs:/app/logs
   ```
3. Измените команду запуска:
   ```yaml
   command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Production

Для продакшена рекомендуется:

1. Использовать отдельный файл `docker-compose.prod.yml`
2. Настроить reverse proxy (nginx)
3. Включить SSL/TLS
4. Установить `DEBUG=false` и `DEV_MODE=false`
5. Использовать secrets для чувствительных данных
6. Настроить автоматические backup'ы БД
7. Настроить monitoring и alerting
